# Market context batches

> **Context-only warning:** Context grouping uses exact Gamma event IDs among rows present in this snapshot. The snapshot may omit event siblings, and shared event membership does not prove proposition, criteria, outcome, or settlement equivalence.

Scan kind: `primary`  
Current proof: `21fcd1a114714c5f75d42a89f79126856479ae3bf290bee620a981bec7f329be`  
Source integrity verified: `True`  
Prior proof: `2f659a7b3cecc4001f445eb5964cb85fe7ff3118b010af6dd5aff2a41609a39c`

Upstream discovery coverage: `{"fetch": {"duplicate_market_rows": 0, "endpoint": "markets", "fetched_market_rows": 1000, "malformed_rows": 0, "max_pages": 10, "pages_attempted": 10, "pages_succeeded": 10, "pagination_complete": false, "response_rows": 1000, "stop_reason": "page_cap"}, "filters": {"eligible_before_top": 599, "filter_accounting_complete": true, "filter_rejections": {"horizon": 48, "liquidity": 263, "missing_deadline": 2, "past_deadline": 86, "spread": 2}, "input_markets": 1000, "selected": 80, "selection_complete": false, "top_omitted": 519}}`
Minimum order size is in shares; legacy `min_size_usd` is a share-count alias.

Warnings:
- 6 prior market(s) are absent from the current filtered shortlist; omission is not evidence of closure or resolution
- upstream discovery pagination is incomplete: page_cap
- upstream output cap omitted 519 eligible rows

## Batch 1 (19 markets)

### Almaty Open: Mikhail Kukushkin vs Stefanos Sakellaridis
Group basis: `exact_gamma_event_id`; event ID: `1212791`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 1 | changed | Almaty Open: Mikhail Kukushkin vs Stefanos Sakellaridis [market=5893068; condition=0x76a7b37b0897c0e3d9775fad0dd51a4a01a27e7d1c08b0a54d4b3e7c1dda2aef] | Mikhail Kukushkin=0.9995, Stefanos Sakellaridis=0.0005 | tick, best_ask, best_bid, outcome_prices | True | `fa5ff128bfbb8c7d52f994308f6881e5aabd0882535281d8bd2e823de05303bd` |

### Lyon Open: Matteo Arnaldi vs Lorenzo Musetti
Group basis: `exact_gamma_event_id`; event ID: `1208077`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 2 | changed | Lyon Open: Matteo Arnaldi vs Lorenzo Musetti [market=5843258; condition=0x3f83cbaecd0b8e7e1e1aeca689258b72556975ee94f790c94d756b7e77301b93] | Matteo Arnaldi=0.0005, Lorenzo Musetti=0.9995 | tick, best_ask, best_bid, outcome_prices | True | `876c0ddbe6ed0eb19db05841ec817bdc5ac9f17d465f8a7a9f63c10af07f1008` |

### Counter-Strike: PARIVISION vs magic (BO3) - 1win Private Club #2 Playoffs
Group basis: `exact_gamma_event_id`; event ID: `1177849`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 3 | changed | Counter-Strike: PARIVISION vs magic (BO3) - 1win Private Club #2 Playoffs [market=5611345; condition=0xdf508a4aac730589160b38faf501a6ac30f71818232c94380c0afb540adaf0fe] | PARIVISION=0.575, magic=0.425 | end_date | True | `b235e0765e317aa87b5d98e59468005cbc0894e43df49978ec2f2f67bf30fd8e` |

### Commanders vs. 49ers
Group basis: `exact_gamma_event_id`; event ID: `987958`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 4 | new_to_snapshot | Spread: Commanders (-3.5) [market=5130444; condition=0xebacd0a96dcea2338cf7e52637ec95ec45810c0b3ab4fc56fa1b88734d0ed6c4] | Commanders=0.115, 49ers=0.885 | new_to_snapshot | True | `6861a2a123c63a356e630c1a4baba68db018b09740fcdf79a9893bc2da82f36c` |
| context | context_unchanged | Commanders vs. 49ers [market=4362230; condition=0xe899447d5c12318b14d086ce50f9efe77ae8db953b4e937f155e68ac0de8cc82] | Commanders=0.215, 49ers=0.785 |  | True | `311d82478caba62d146221d8bc5206a7fee2ddd0785f8774ac417119269a0e89` |
| context | context_unchanged | Commanders vs. 49ers: O/U 52.5 [market=5130621; condition=0xeb40ee36d8e2086a11a440af14e33e9a41b7772ed5a02168c9d5df6dd0c61d0d] | Over=0.465, Under=0.535 |  | True | `dae63435529914ef133d540c228e9166ab6e181418860f464908b86de5ad20b9` |

### Balance of Power: 2026 Midterms
Group basis: `exact_gamma_event_id`; event ID: `32228`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 5 | new_to_snapshot | 2026 Balance of Power: D Senate, D House [market=562828; condition=0x16c63b7cc37f012b9f59ee164ec03877914c701d06d48291ae8d6fc08a088b0d] | Yes=0.625, No=0.375 | new_to_snapshot | True | `3c3ecb4df30ab75947e175859e78d40d0f89e03185af275a72b70ed349dc599e` |
| context | context_unchanged | 2026 Balance of Power: D Senate, R House [market=562829; condition=0x0808de4f0cfd47947f2d1be51f9a9c52ea0fec76f73a75cfbe79ddec98d8a908] | Yes=0.0095, No=0.9905 |  | True | `79a74a08a2da8da9e6ad0838263fa2dff6b9232261e9187e2ee304bf056c1b86` |

### Counter-Strike: Betclic Apogee Esports vs BBL (BO3) - PGL Bucharest Closed Qualifier Playoffs
Group basis: `exact_gamma_event_id`; event ID: `1207260`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 6 | new_to_snapshot | Counter-Strike: Betclic Apogee Esports vs BBL (BO3) - PGL Bucharest Closed Qualifier Playoffs [market=5834571; condition=0x18b3374a5f9aab496b868d144c92c60286098c1e013b7e4329d49179415085bc] | Betclic Apogee Esports=0.005, BBL=0.995 | new_to_snapshot | True | `d1f138410e94974c0901a8676243fc043a5c839bb7c1397e8dd5ae181a386bcd` |

### Ballon d'Or Winner 2026
Group basis: `exact_gamma_event_id`; event ID: `48361`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 7 | new_to_snapshot | Will Ousmane Dembélé win the 2026 Ballon d'Or? [market=608543; condition=0x26f410f7518fa199678ef57f02637fc88be9b3b593346b00946d7ea451f4521b] | Yes=0.0015, No=0.9985 | new_to_snapshot | True | `2757e7cba600ebe133c27bfd89ddee37751de6e91d8971262cfa437b568ab66f` |
| context | context_unchanged | Will Kylian Mbappé win the 2026 Ballon d'Or? [market=608540; condition=0x87091dc5932f015d80c40e71e47cb043c3f8b6098484eb5bc3943cf35ee9afc1] | Yes=0.0345, No=0.9655 |  | True | `8c981e7fc9d2bf7d9115639c687f5f8a2e331e2e7e7c83cfeb742ec202c9b688` |
| context | context_unchanged | Will Erling Haaland win the 2026 Ballon d'Or? [market=608541; condition=0xc89266786402aaabe78111eb91c6764d86857bbc4427c82b91d60a5ef69a70d0] | Yes=0.0015, No=0.9985 |  | True | `4ae670c3f7e275f2a97ce11d98c61bd47b3c0f1e4f780d19984c26a95233c4d7` |
| context | context_unchanged | Will Lamine Yamal win the 2026 Ballon d'Or? [market=608545; condition=0xa34edb6c898232378a9cc08744842df2cd89d278ba45b012bed3ac10c7241c4d] | Yes=0.2375, No=0.7625 |  | True | `1cd13c0ef791fa236b3ca9e7d571089a7dbf2c447c8450b60e3896edc541534e` |
| context | context_unchanged | Will Harry Kane win the 2026 Ballon d'Or? [market=608547; condition=0x12dc2b61723b2a54fc1947a307389b5f32038e7a29a0e936ad1fe410b969d06a] | Yes=0.6895, No=0.3105 |  | True | `9713dc20cbfe8ffd2219d43212e8943227ffd5a3c57a2884532af31ccd8fdd2e` |
| context | context_unchanged | Will Lionel Messi win the 2026 Ballon d'Or? [market=608565; condition=0x7034c00a24f9edbf325fd5a0b9a63412e469fc8cd2aa9b060fb5ba8e10d7ebef] | Yes=0.0305, No=0.9695 |  | True | `2b4489e92845ca04744512e22464ca9c56852c8a3f48b699e6769d150fe166b1` |

### Tottenham Hotspur FC vs. Coventry City FC - More Markets
Group basis: `exact_gamma_event_id`; event ID: `1141211`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 8 | new_to_snapshot | Spread: Tottenham Hotspur FC (-1.5) [market=5364544; condition=0xb751a15dca71c2d9e8b71642de29e5fcf396ed085131eba4a38d56bb18918d43] | Tottenham Hotspur FC=0.385, Coventry City FC=0.615 | new_to_snapshot | True | `6944a6d309e992fb38189220ac793d8e534cb77bed73d9368e589b3486da2d35` |

### What will WTI Crude Oil (WTI) hit in October 2026?
Group basis: `exact_gamma_event_id`; event ID: `1078055`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 9 | new_to_snapshot | Will WTI Crude Oil (WTI) hit (HIGH) $105 in October? [market=4951227; condition=0x33f529b87bb00a1ff2a948694a0b72cb67f8e267246c9e7658bb6198eb2d9af4] | Yes=0.415, No=0.585 | new_to_snapshot | True | `0944ccf0c6c9c187dd1b301445b591145d33dfaac1c61ca6c4d7dec970b1e11f` |

### US-Iran ceasefire continues through...?
Group basis: `exact_gamma_event_id`; event ID: `1038648`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 10 | changed | US x Iran ceasefire continues through October 31? [market=4641065; condition=0x3738ad9665480991affe3ba286cd035516e17d1f8b7703e05088ec19c70c21a4] | Yes=0.62, No=0.38 | best_ask, best_bid, no_price, yes_price, outcome_prices | True | `9f80a705fbb60efe9ea18e1edee1b2fe66f566a43b006fe0e52bd2294c1763c8` |
| context | context_unchanged | US x Iran ceasefire continues through October 22? [market=5686979; condition=0x04fb634139d4654febf4b62c425b209806e06d9eff93ac2e7c5301ecdaf5e4ca] | Yes=0.737, No=0.263 |  | True | `7169d5cefc7e3cbea8f29a8854a965693341f50f73d02090b14458a1d82dcdfd` |

## Batch 2 (3 markets)

### Counter-Strike: fnatic vs Liquid (BO3) - 1win Private Club #2 Playoffs
Group basis: `exact_gamma_event_id`; event ID: `1177848`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 11 | changed | Counter-Strike: fnatic vs Liquid - Map 2 Winner [market=5611333; condition=0x9fb7ba21e48079951c7a688bffde2768f0997f5d4e6604852dff174bd0d29447] | fnatic=0.9995, Liquid=0.0005 | best_ask, best_bid, outcome_prices | True | `84a88cec33d7489c6b4347db3eac35a7c4509cf6c5c23c5d66713e1fadd0cf6c` |
| context | context_unchanged | Counter-Strike: fnatic vs Liquid (BO3) - 1win Private Club #2 Playoffs [market=5611334; condition=0x70e8faf2eb653b69866cb27a59afba35c19fd05a686d32ae8b3c15e6f0ce2add] | fnatic=0.9995, Liquid=0.0005 |  | True | `580ed5310a318e61b1d166bc9d7bc23c5aff791dccf9730827d67fcbf951e912` |

### US-Iran ceasefire continues through the midterms?
Group basis: `exact_gamma_event_id`; event ID: `1156710`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 12 | changed | US-Iran ceasefire continues through the midterms? [market=5447182; condition=0x613613192c69d90cee89758c260a019368fc1f4a596b4d300c39b6235d2b643f] | Yes=0.63, No=0.37 | best_ask, best_bid, no_price, yes_price, outcome_prices | True | `a35ea08362d004cfd645499651bec8abe6d3b4503071f2d8d1b321bffe5b53d9` |
