import gzip
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import deep_review_economics as economics


class DeepReviewEconomicsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.root = Path(self.temp.name)
        (self.root / "notes").mkdir()
        (self.root / "notes/aave_hurdle.json").write_text(json.dumps({"apy": 0.03}))
        self.frozen = {
            "review_index": 275,
            "id": "market-275",
            "slug": "market-275-frozen-slug",
            "conditionId": "0xabc275",
            "question": "Frozen question?",
            "description": "Frozen exact criteria text.",
            "resolutionSource": "https://example.test/source",
            "endDate": "2026-12-31T17:00:00Z",
            "outcomes": '["Yes", "No"]',
            "clobTokenIds": '["yes-token", "no-token"]',
            "criteria_sha256": "a" * 64,
        }
        self.root_patch = patch.object(economics, "ROOT", self.root)
        self.ledger_patch = patch.object(economics.ledger, "universe", return_value={275: self.frozen})
        self.root_patch.start()
        self.ledger_patch.start()

    def tearDown(self):
        self.ledger_patch.stop()
        self.root_patch.stop()
        self.temp.cleanup()

    def make_packet(self, *, reversed_books=False, book_age_ms=0):
        received = "2026-10-18T19:58:35.000+00:00"
        received_epoch_ms = int(datetime.fromisoformat(received).replace(tzinfo=timezone.utc).timestamp() * 1000)
        books = []
        returned = []
        frozen_outcomes = json.loads(self.frozen["outcomes"])
        frozen_tokens = json.loads(self.frozen["clobTokenIds"])
        for outcome, token in zip(frozen_outcomes, frozen_tokens):
            book = {
                "market": self.frozen["conditionId"], "asset_id": token,
                "timestamp": str(received_epoch_ms - book_age_ms), "hash": f"hash-{token}",
                "bids": [{"price": "0.4", "size": "20"}],
                "asks": [{"price": "0.5", "size": "20"}],
                "min_order_size": "5", "tick_size": "0.01",
                "neg_risk": False, "last_trade_price": "0.45",
            }
            returned.append(book)
            books.append({"outcome": outcome, "token_id": token, "request_id": "batch-1",
                          "received_utc": received, "available": True, "book": book})
        if reversed_books:
            books.reverse()
        raw_body = json.dumps(returned, separators=(",", ":")).encode()
        compressed = gzip.compress(raw_body)
        (self.root / "book.json.gz").write_bytes(compressed)
        receipt = {
            "request_id": "batch-1", "method": "POST", "url": "https://clob.polymarket.com/books",
            "status_code": 200, "received_utc": received,
            "json_request_body": [{"token_id": token} for token in frozen_tokens],
            "gzip_path": "book.json.gz", "gzip_sha256": hashlib.sha256(compressed).hexdigest(),
            "raw_sha256": hashlib.sha256(raw_body).hexdigest(),
        }
        (self.root / "receipt.json").write_text(json.dumps(receipt))
        gamma = {
            "id": self.frozen["id"], "conditionId": self.frozen["conditionId"],
            "slug": self.frozen["slug"],
            "question": self.frozen["question"], "description": self.frozen["description"],
            "resolutionSource": self.frozen["resolutionSource"], "endDate": self.frozen["endDate"],
            "outcomes": self.frozen["outcomes"], "clobTokenIds": self.frozen["clobTokenIds"],
            "feeSchedule": {"rate": 0.0, "exponent": 1.0, "takerOnly": True},
        }
        gamma_raw = json.dumps(gamma, separators=(",", ":")).encode()
        gamma_gzip = gzip.compress(gamma_raw)
        (self.root / "gamma.json.gz").write_bytes(gamma_gzip)
        gamma_received = "2026-10-18T19:58:34.000+00:00"
        gamma_receipt = {
            "request_id": "gamma-1", "method": "GET",
            "url": "https://gamma-api.polymarket.com/markets/market-275",
            "status_code": 200, "received_utc": gamma_received,
            "started_utc": "2026-10-18T19:58:33.000+00:00",
            "gzip_path": "gamma.json.gz",
            "gzip_sha256": hashlib.sha256(gamma_gzip).hexdigest(),
            "raw_sha256": hashlib.sha256(gamma_raw).hexdigest(),
        }
        (self.root / "gamma.receipt.json").write_text(json.dumps(gamma_receipt))
        case = {
            "review_index": 275, "criteria_exact_match": True,
            "frozen_identity": {"market_id": self.frozen["id"], "condition_id": self.frozen["conditionId"],
                                "criteria_sha256": self.frozen["criteria_sha256"]},
            "identity_checks": {k: True for k in ("market_id", "condition_id", "question", "description", "outcomes", "token_ids")},
            "current_gamma": gamma,
            "gamma_receipt": {"path": "gamma.receipt.json", "status_code": 200,
                              "received_utc": gamma_received,
                              "raw_sha256": hashlib.sha256(gamma_raw).hexdigest()},
            "books": books,
        }
        packet = {"created_utc": "2026-10-18T19:58:35.001+00:00", "cases": [case],
                  "clob_transport_receipts": [{"type": "books_batch", "request_id": "batch-1",
                       "status_code": 200, "received_utc": received, "receipt_path": "receipt.json"}]}
        path = self.root / "packet.json"
        path.write_text(json.dumps(packet))
        return path, packet, case

    def rewrite_gamma_receipt(self, case):
        """Make a self-consistent captured Gamma response for frozen checks."""
        raw = json.dumps(case["current_gamma"], separators=(",", ":")).encode()
        compressed = gzip.compress(raw)
        (self.root / "gamma.json.gz").write_bytes(compressed)
        receipt = json.loads((self.root / "gamma.receipt.json").read_text())
        receipt["gzip_sha256"] = hashlib.sha256(compressed).hexdigest()
        receipt["raw_sha256"] = hashlib.sha256(raw).hexdigest()
        (self.root / "gamma.receipt.json").write_text(json.dumps(receipt))
        case["gamma_receipt"]["raw_sha256"] = receipt["raw_sha256"]

    def test_book_age_uses_matching_receipt_and_threshold_is_output(self):
        path, _, case = self.make_packet(book_age_ms=180_000)
        result = economics.economics(275, 0.7, path)
        self.assertAlmostEqual(result["sides"]["Yes"]["book_age_seconds_at_receipt"], 180.0, places=5)
        self.assertTrue(result["sides"]["Yes"]["passed_180s_at_receipt"])
        self.assertEqual(result["sides"]["Yes"]["book_received_utc"], "2026-10-18T19:58:35.000+00:00")
        self.assertNotEqual(result["sides"]["Yes"]["book_received_utc"], case["gamma_receipt"]["received_utc"])
        stale, _, _ = self.make_packet(book_age_ms=180_001)
        self.assertFalse(economics.economics(275, 0.7, stale)["sides"]["Yes"]["passed_180s_at_receipt"])

    def test_reordered_books_keep_probability_bound_to_named_outcome(self):
        path, _, _ = self.make_packet(reversed_books=True)
        result = economics.economics(275, 0.7, path)
        self.assertEqual(result["sides"]["Yes"]["probability"], 0.7)
        self.assertAlmostEqual(result["sides"]["No"]["probability"], 0.3)
        self.assertEqual(result["probability_reference_outcome"], "Yes")

    def test_explicit_named_reference_survives_reversed_book_order(self):
        self.frozen["outcomes"] = '["Kylian Mbappe", "Lamine Yamal"]'
        self.frozen["clobTokenIds"] = '["mbappe-token", "yamal-token"]'
        path, _, _ = self.make_packet(reversed_books=True)
        result = economics.economics(275, 0.7, path, reference_outcome="Lamine Yamal")
        self.assertEqual(result["probability_reference_outcome"], "Lamine Yamal")
        self.assertEqual(result["sides"]["Lamine Yamal"]["probability"], 0.7)
        self.assertAlmostEqual(result["sides"]["Kylian Mbappe"]["probability"], 0.3)

    def test_non_yes_no_labels_require_exact_reference(self):
        self.frozen["outcomes"] = '["Mbappe", "Yamal"]'
        self.frozen["clobTokenIds"] = '["mbappe-token", "yamal-token"]'
        path, _, _ = self.make_packet()
        with self.assertRaisesRegex(ValueError, "reference_outcome is required"):
            economics.economics(275, 0.7, path)
        with self.assertRaisesRegex(ValueError, "exactly match"):
            economics.economics(275, 0.7, path, reference_outcome="mbappe")
        with self.assertRaisesRegex(ValueError, "label string"):
            economics.economics(275, 0.7, path, reference_outcome=1)

    def test_more_than_two_labels_fails_before_probability_assignment(self):
        self.frozen["outcomes"] = '["A", "B", "C"]'
        self.frozen["clobTokenIds"] = '["a-token", "b-token", "c-token"]'
        path, _, _ = self.make_packet()
        with self.assertRaisesRegex(ValueError, "exactly two"):
            economics.economics(275, 0.7, path, reference_outcome="A")

    def test_exact_frozen_identity_and_hashed_returned_book_are_checked(self):
        path, packet, case = self.make_packet()
        economics.quote(275, path)
        case["current_gamma"]["description"] = "Altered criteria"
        self.rewrite_gamma_receipt(case)
        path.write_text(json.dumps(packet))
        with self.assertRaisesRegex(ValueError, "Gamma description differs"):
            economics.quote(275, path)
        case["current_gamma"]["description"] = self.frozen["description"]
        case["current_gamma"]["clobTokenIds"] = '["fake-token", "no-token"]'
        self.rewrite_gamma_receipt(case)
        path.write_text(json.dumps(packet))
        with self.assertRaisesRegex(ValueError, "outcome/token"):
            economics.quote(275, path)
        case["current_gamma"]["clobTokenIds"] = self.frozen["clobTokenIds"]
        self.rewrite_gamma_receipt(case)
        case["books"][0]["book"]["timestamp"] = "1"
        path.write_text(json.dumps(packet))
        with self.assertRaisesRegex(ValueError, "differs from the hashed CLOB response"):
            economics.quote(275, path)
        case["books"][0]["book"]["timestamp"] = case["books"][1]["book"]["timestamp"]
        raw = json.loads(gzip.decompress((self.root / "book.json.gz").read_bytes()))
        raw[0]["timestamp"] = "tampered-body-row"
        raw_bytes = json.dumps(raw, separators=(",", ":")).encode()
        compressed = gzip.compress(raw_bytes)
        (self.root / "book.json.gz").write_bytes(compressed)
        receipt = json.loads((self.root / "receipt.json").read_text())
        receipt["gzip_sha256"] = hashlib.sha256(compressed).hexdigest()
        receipt["raw_sha256"] = hashlib.sha256(raw_bytes).hexdigest()
        (self.root / "receipt.json").write_text(json.dumps(receipt))
        path.write_text(json.dumps(packet))
        with self.assertRaisesRegex(ValueError, "differs from the hashed CLOB response"):
            economics.quote(275, path)

    def test_missing_mismatched_or_invalid_receipt_metadata_fails_closed(self):
        path, packet, case = self.make_packet()
        case["books"][0].pop("received_utc")
        path.write_text(json.dumps(packet))
        with self.assertRaisesRegex(ValueError, "missing book row received_utc"):
            economics.quote(275, path)
        case["books"][0]["received_utc"] = "2026-10-18T19:58:36Z"
        path.write_text(json.dumps(packet))
        with self.assertRaisesRegex(ValueError, "does not match its receipt"):
            economics.quote(275, path)
        case["books"][0]["received_utc"] = "2026-10-18T19:58:35Z"
        gamma_receipt_path = self.root / "gamma.receipt.json"
        gamma_receipt = json.loads(gamma_receipt_path.read_text())
        gamma_receipt["started_utc"] = "2026-10-18T19:58:35Z"
        gamma_receipt_path.write_text(json.dumps(gamma_receipt))
        path.write_text(json.dumps(packet))
        with self.assertRaisesRegex(ValueError, "precedes request start"):
            economics.quote(275, path)
        gamma_receipt["started_utc"] = "2026-10-18T19:58:33Z"
        gamma_receipt_path.write_text(json.dumps(gamma_receipt))
        receipt = json.loads((self.root / "receipt.json").read_text())
        receipt["url"] = "https://example.test/books"
        (self.root / "receipt.json").write_text(json.dumps(receipt))
        path.write_text(json.dumps(packet))
        with self.assertRaisesRegex(ValueError, "expected CLOB POST endpoint"):
            economics.quote(275, path)

    def test_gamma_fee_body_and_receipt_target_are_bound(self):
        path, packet, case = self.make_packet()
        economics.quote(275, path)
        # Fee data is consumed by economics even though it is not frozen identity.
        case["current_gamma"]["feeSchedule"]["rate"] = 0.2
        path.write_text(json.dumps(packet))
        with self.assertRaisesRegex(ValueError, "captured Gamma market differs"):
            economics.quote(275, path)

        case["current_gamma"]["feeSchedule"]["rate"] = 0.0
        receipt_path = self.root / "gamma.receipt.json"
        receipt = json.loads(receipt_path.read_text())
        receipt["url"] = "https://gamma-api.polymarket.com/markets/other-market"
        receipt_path.write_text(json.dumps(receipt))
        path.write_text(json.dumps(packet))
        with self.assertRaisesRegex(ValueError, "exact frozen-market endpoint"):
            economics.quote(275, path)

        receipt["url"] = "https://gamma-api.polymarket.com/markets/market-275"
        receipt_path.write_text(json.dumps(receipt))
        gamma_body_path = self.root / "gamma.json.gz"
        changed = json.loads(gzip.decompress(gamma_body_path.read_bytes()))
        changed["feeSchedule"]["rate"] = 0.2
        altered_raw = json.dumps(changed, separators=(",", ":")).encode()
        altered_gzip = gzip.compress(altered_raw)
        gamma_body_path.write_bytes(altered_gzip)
        # Receipt hashes deliberately remain unchanged: corrupt body must fail.
        path.write_text(json.dumps(packet))
        with self.assertRaisesRegex(ValueError, "gzip hash mismatch"):
            economics.quote(275, path)

    def test_gamma_slug_is_exactly_frozen(self):
        path, packet, case = self.make_packet()
        case["current_gamma"]["slug"] = "different-market-slug"
        self.rewrite_gamma_receipt(case)
        path.write_text(json.dumps(packet))
        with self.assertRaisesRegex(ValueError, "Gamma slug differs"):
            economics.quote(275, path)

    def test_invalid_probabilities_and_quantity_fail_closed(self):
        path, _, _ = self.make_packet()
        for kwargs in ({"p_yes": 1.01}, {"p_yes": float("nan")}, {"p_yes": .5, "quantity": 0}):
            with self.assertRaises(ValueError):
                economics.economics(275, quote_path=path, **kwargs)


if __name__ == "__main__":
    unittest.main()
