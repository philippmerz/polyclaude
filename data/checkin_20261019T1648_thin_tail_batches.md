# Market context batches

> **Context-only warning:** Context grouping uses exact Gamma event IDs among rows present in this snapshot. The snapshot may omit event siblings, and shared event membership does not prove proposition, criteria, outcome, or settlement equivalence.

Scan kind: `thin_tail`  
Current proof: `c594fcb2996c8d685ca71c817c6291ecd95ddb36608342180ff428795a30c44e`  
Source integrity verified: `True`  
Prior proof: `69ffc651678d6dc4fc3576337b6b17ccf470acf2a4c4252ab3d9613df1975838`

Upstream discovery coverage: `{"fetch": {"duplicate_market_rows": 241, "endpoint": "events", "fetched_market_rows": 38975, "malformed_rows": 0, "max_pages": 20, "pages_attempted": 20, "pages_succeeded": 20, "pagination_complete": false, "response_rows": 2000, "stop_reason": "page_cap"}, "filters": {"eligible_before_top": 3297, "filter_accounting_complete": true, "filter_rejections": {"horizon": 322, "liquidity": 15069, "missing_deadline": 25, "not_tradable": 5762, "past_deadline": 1014, "spread": 804, "volume": 9837, "win_assumed_hurdle": 2845}, "input_markets": 38975, "selected": 3000, "selection_complete": false, "top_omitted": 297}}`
Minimum order size is in shares; legacy `min_size_usd` is a share-count alias.

Warnings:
- 197 prior market(s) are absent from the current filtered shortlist; omission is not evidence of closure or resolution
- upstream discovery pagination is incomplete: page_cap
- upstream output cap omitted 297 eligible rows

## Batch 1 (17 markets)

### What will OpenAI's IPO valuation be?
Group basis: `exact_gamma_event_id`; event ID: `507875`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 1 | new_to_snapshot | Will OpenAI's IPO valuation be between $1.0T and $1.25T? [market=2316999; condition=0x956d27f8f2a7f952312c5b94ca9c32c9ecb31fea8cf808d2f970702e2636ec73] | Yes=0.0555, No=0.9445 | new_to_snapshot | True | `94ce0928aa6717c8d7d7b11d9ec67445a41de99388aedee6fe0a807de71cd292` |

### Premier League: Teams relegated (2026-27)
Group basis: `exact_gamma_event_id`; event ID: `904907`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 2 | new_to_snapshot | Will Manchester City be relegated from the 2026-27 Premier League? [market=3848389; condition=0x5142be04c728f39973e57d51c32260e86b3eb88d323d3369e551f41644c92288] | Yes=0.358, No=0.642 | new_to_snapshot | True | `576733fe94f264faf1fe022437ce9d915b741126cb8446c12f1c6695df360a48` |
| 52 | new_to_snapshot | Will Crystal Palace be relegated from the 2026-27 Premier League? [market=3848373; condition=0xb743beadd988fdaa9de48de58af4203e65e3acd1b7f2da263e5665b31f0166b3] | Yes=0.315, No=0.685 | new_to_snapshot | True | `840a8e885db9bed2ef9db401d40bac37f34d3ee32c0765a170aa10db68b8c790` |
| context | context_unchanged | Will Coventry City be relegated from the 2026-27 Premier League? [market=3848371; condition=0xb5ccec7b66d713656f8e259841d821b12191f844e9971dc338679fb0ebc000aa] | Yes=0.55, No=0.45 |  | True | `c5297b3d2bc525ee5f474bf4baaed9bad16e91c1f32b7bd4fbde45d4750a2403` |
| context | context_unchanged | Will Fulham be relegated from the 2026-27 Premier League? [market=3848377; condition=0xd5a30872772c9b6e11eb8e03fb20e3d0a9c22b629a41bd910736c063b1453ab5] | Yes=0.28, No=0.72 |  | True | `746890e4cabe95305420b2d31e4b3b276d2b43c961bbf9c45c0d367dad1e1ee1` |
| context | context_unchanged | Will Hull City be relegated from the 2026-27 Premier League? [market=3848379; condition=0x1587b261f0687397f09d8ee54ef4e36abdd77d280fb8e28bad6e60b462b8a786] | Yes=0.545, No=0.455 |  | True | `4094c0af40c4e95734b1cf4e958ab5dae47412200bc71b71ec063cdab2cb8560` |
| context | context_unchanged | Will Tottenham Hotspur be relegated from the 2026-27 Premier League? [market=3848400; condition=0xc4debf10b85f92ac6eb9a7ae9546f3c421b2efd21c0c286a1426082ee1971bd5] | Yes=0.13, No=0.87 |  | True | `c1a775b0bf9c9835d9f3dc68700ecbb6e606e8c6dd8cf00f8d53b8e5c5c70908` |

### When will the Rhine River return to normal levels?
Group basis: `exact_gamma_event_id`; event ID: `976810`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 3 | new_to_snapshot | Will the Rhine River return to normal levels between October 1 and October 31, 2026? [market=4294627; condition=0xa52beb533967265e4abce442e554e9d0b556c9ee4f2a3cb97d2bd915acc23652] | Yes=0.735, No=0.265 | new_to_snapshot | True | `c02a36b7cbff1c5e71fbeb2ee8e6e7581aac18ea76d53e2a9b67abe174e2ed11` |
| context | context_unchanged | Will the Rhine River fail to return to normal levels before November 1, 2026? [market=4294628; condition=0x93bea8cddd9c3df9019d6e3868aa86058377e8a274c6c1060c4a317110c88172] | Yes=0.255, No=0.745 |  | True | `4d500b2752c5fc192b876205d6038d67d1e69924bae43d713c541cd655ba0318` |

### DICK'S Sporting Goods Q3 Dick's business comparable sales growth?
Group basis: `exact_gamma_event_id`; event ID: `1194150`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 4 | new_to_snapshot | Will DICK'S Sporting Goods Q3 Dick's business comparable sales growth be between 3% and 4%? [market=5730354; condition=0x72930461dfd7b3729b29b5d040de9678c6949ae00e8ecd3a5ca5ce8d41b0d62f] | Yes=0.455, No=0.545 | new_to_snapshot | True | `1d4c2b3686a162e68e9e2968d8d993691959d63cb4378fac60f0148bc07473de` |
| 6 | new_to_snapshot | Will DICK'S Sporting Goods Q3 Dick's business comparable sales growth be above 4%? [market=5730355; condition=0x4e275999af6be0df9f62ac35428d478026765b820a0bb8df782e906c5d7324ec] | Yes=0.295, No=0.705 | new_to_snapshot | True | `9efa709c8317c4f8adfa6789a30e49b65dda61ccc241b737c06cd08fe855ad7a` |
| context | context_unchanged | Will DICK'S Sporting Goods Q3 Dick's business comparable sales growth be below 1%? [market=5730351; condition=0x548a125bf3117f553ae9af514732b5c64623ba6b5295bb81d59191988de16410] | Yes=0.0155, No=0.9845 |  | True | `6092b622bb0e0746990f05db46407cdd94bc92c4ddee8fbc2438fc2fab78a163` |

### Virginia Senate Election: Turnout
Group basis: `exact_gamma_event_id`; event ID: `870917`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 5 | new_to_snapshot | Will total votes cast in the 2026 midterm election for Senator from Virginia be between 3,500,000 and 3,750,000? [market=3697770; condition=0x8a9b48f934fd4bf28a87980dc0c5b1987a3ba06a5a171456ada53f4ce774244b] | Yes=0.3965, No=0.6035 | new_to_snapshot | True | `9aa67151e8f25cf0fffc600e912537ab5f7e3a5bf3ca819d5a08da9c73135442` |
| context | context_unchanged | Will total votes cast in the 2026 midterm election for Senator from Virginia be between 2,500,000 and 2,750,000? [market=3697766; condition=0x5aa6ca99d1cbdc54377e5cd48d075aba04b8dcbafc94f06c906af71c613a5814] | Yes=0.07, No=0.93 |  | True | `cdbf6e126fa406249a2dde37a1334fac3c7cd6da6eb23779d6ffc4c8c9d035ba` |

### Next Claude Haiku Model (4.6+): Text Arena Debut?
Group basis: `exact_gamma_event_id`; event ID: `1111228`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 7 | new_to_snapshot | Will the next Claude Haiku model (4.6+) debut at a score of at least 1440 by June 30, 2027? [market=5167103; condition=0x3a2e70ca0e2ef6e81ea24c749affe96f7cc2218f665e4feab8b5208453cb6a47] | Yes=0.77, No=0.23 | new_to_snapshot | True | `e126b86bd361cb755bc3ef950c894ccb097c6273f4b430a42ba79878a62341ef` |
| context | context_unchanged | Will the next Claude Haiku model (4.6+) debut at a score of at least 1420 by June 30, 2027? [market=5167102; condition=0xdde540c3ca18f2ae9102c7bd4099d9e9b9a88897610a8b512aa1b6028f5ab993] | Yes=0.855, No=0.145 |  | True | `c9c80a28f3c54e373b59ea9025804bf5b94a1224dd7475e1a7c3f79d260dd6c4` |
| context | context_unchanged | Will the next Claude Haiku model (4.6+) debut at a score of at least 1460 by June 30, 2027? [market=5167104; condition=0x06fd2104695d577073c504d31b1fcbd30955d00d06cc2fabac6e2e8b695d484d] | Yes=0.11, No=0.89 |  | True | `43210d837a8266fdc694f6d32957f2c2fb28c59b5922b045d2cec0175547d3bc` |

## Batch 2 (16 markets)

### What will Meta Platforms, Inc. (META) hit Week of October 19 2026?
Group basis: `exact_gamma_event_id`; event ID: `1202019`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 8 | new_to_snapshot | Will Meta Platforms, Inc. (META) hit (HIGH) $750 Week of October 19 2026? [market=5788750; condition=0x25fdc4726eb5ebc2efd47a2ab72c0b9817811161a1d9c791821dc6c2ce712ed6] | Yes=0.42, No=0.58 | new_to_snapshot | True | `1021a3a45057ba21e2701d82d211521320ad4aedb703e3ca62eb0962c4d612e8` |
| context | context_unchanged | Will Meta Platforms, Inc. (META) hit (HIGH) $710 Week of October 19 2026? [market=5788756; condition=0xa6b432f4546e9ab03a33137c4c34f844e8ba6d26c4e1e67d986f7d469763cd5d] | Yes=0.836, No=0.164 |  | True | `d0a367bf5bd43c61967dd70bbab058988e32d55238a50157b01cfd294dd78ac9` |
| context | context_unchanged | Will Meta Platforms, Inc. (META) hit (LOW) $690 Week of October 19 2026? [market=5788758; condition=0x546e2cf7974bebd8ffe260971cb05013b51baf3f50a4543c12538effa3a1d161] | Yes=0.805, No=0.195 |  | True | `62c429e94397c39d95e2bd1212c7f37890c5f7b63adeca021e24f26bc9245d93` |
| context | context_unchanged | Will Meta Platforms, Inc. (META) hit (LOW) $680 Week of October 19 2026? [market=5788759; condition=0x97030620572679fa5a0536c51d9c6eb925fa0eddf91cb443a5e308d7afdd07ea] | Yes=0.68, No=0.32 |  | True | `d2ece1a1f5654a0df348d794cc1ff6e756393761cae51d16b184e6ac02afafde` |
| context | context_unchanged | Will Meta Platforms, Inc. (META) hit (LOW) $650 Week of October 19 2026? [market=5788762; condition=0xdb6d99ceddcde2c888e02635a889ecf5650948223348392aac4a1631a41fab41] | Yes=0.355, No=0.645 |  | True | `36ad391bb22d16237ca4f34d6be5b19b213700c92c7b8bdc73a97621172142d8` |

### Next Israeli Minister of Foreign Affairs?
Group basis: `exact_gamma_event_id`; event ID: `1107820`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 9 | new_to_snapshot | Will Gideon Sa’ar be the next Israeli Minister of Foreign Affairs? [market=5151684; condition=0xce4a2d67ed58e2040e219e6425268a8c3d864baea26481d815286177ef317ff0] | Yes=0.026, No=0.974 | new_to_snapshot | True | `4ecc532e2cecf07d503fe40097e0dcdf9493a5131db64843a1be38da85b52485` |
| 215 | changed | Will Yair Lapid be the next Israeli Minister of Foreign Affairs? [market=5151685; condition=0xc9c45970a2b948e7071f4e92791b76dd4e95b8bfc86f6805780f60cdcfcb7e22] | Yes=0.245, No=0.755 | best_bid, no_price, spread, yes_price, outcome_prices | True | `76ce798f9bb462aa547d06e10ebc6c3bf5743f9ba4fb69d9ae2016739b2fca93` |
| context | context_unchanged | Will Israel Katz be the next Israeli Minister of Foreign Affairs? [market=5151686; condition=0xc3ab0bc73ef5d7fd751c7e38d76cbbb155f07ad1fa21d3a2585e338eb2107993] | Yes=0.08, No=0.92 |  | True | `95db8831121c6b4d35b9866e12b66c38a3ee3080bb94e4a1fa1f1d521b427803` |
| context | context_unchanged | Will Avigdor Lieberman be the next Israeli Minister of Foreign Affairs? [market=5151687; condition=0x78c25ba8028eb376e3eaeb7dd4522e061f5b3d65153a98ef2bd710565ed4a844] | Yes=0.11, No=0.89 |  | True | `c500d2f531d072a5b061b4af7515f7ce29940d366c87cebfbc1f121a0fda3e3a` |
| context | context_unchanged | Will Gadi Eizenkot be the next Israeli Minister of Foreign Affairs? [market=5151692; condition=0x528e6245ca3aa682adf6147face9a8f0fed034708baab334aeb72e3d92e11995] | Yes=0.155, No=0.845 |  | True | `88b66f24fc2d4ea16f911f959b942936791e0683319106827ac28fbbfa562865` |
| context | context_unchanged | Will Naftali Bennett be the next Israeli Minister of Foreign Affairs? [market=5151695; condition=0xf888787c735bf7e83887859de4e8e1b0508bbef6b89fbc92a22e2fbeb0464170] | Yes=0.1, No=0.9 |  | True | `8454cc902bf46107036a658232ea7ea23abdd7f1202ce9fefacfb6bd73b75b78` |
| context | context_unchanged | Will no next Israeli Minister of Foreign Affairs be appointed by February 28, 2027? [market=5151716; condition=0x253393332e4d464542ed2cd55896f6e01b3a2837a7fef3d71759f9c31312609b] | Yes=0.35, No=0.65 |  | True | `985ed4f376227161ae32d079b5f434e36d85ab24639b391fec07f22155d37029` |

### What will NVIDIA (NVDA) hit Week of October 19 2026?
Group basis: `exact_gamma_event_id`; event ID: `1202025`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 10 | new_to_snapshot | Will NVIDIA (NVDA) hit (HIGH) $224 Week of October 19 2026? [market=5788830; condition=0x38da6a2de9a9e6e0bdc11b1b46a6dcacf2b2d52ea9fb06905590cae558da1a73] | Yes=0.5, No=0.5 | new_to_snapshot | True | `bff01237c591d9dced161673c60f8f5a9d2daeba62c31e845092f74d8a193ed9` |
| 218 | changed | Will NVIDIA (NVDA) hit (HIGH) $220 Week of October 19 2026? [market=5788831; condition=0x864b0d66d05be37d91277209bb97219ed9ec1cfc22bc9adcd54b7974bd3aaa82] | Yes=0.805, No=0.195 | best_ask, best_bid, no_price, yes_price, outcome_prices | True | `05327fbc20cd153cda02aa3a9a3ba8bd04c928081d3c43986e9873895fc6fc7e` |
| context | context_unchanged | Will NVIDIA (NVDA) hit (HIGH) $228 Week of October 19 2026? [market=5788829; condition=0x99e9539f21757f6865707aa4c1e28233991ac0524c4cb35d917876c89acf8d85] | Yes=0.26, No=0.74 |  | True | `722a702bf91c8641dae21b41688d673c2dee06119cdfa926e1098a2d1cf07b1f` |
| context | context_unchanged | Will NVIDIA (NVDA) hit (LOW) $212 Week of October 19 2026? [market=5788833; condition=0x9ac7131edf3e4787d2aba278381f354319fc383fb19c3bb322f640a90e24b562] | Yes=0.48, No=0.52 |  | True | `54232313f8153c9906c7b456989ed47d6097927d2caa6483205960a1d6c07d83` |

## Batch 3 (18 markets)

### Best Chinese AI Company end of October?
Group basis: `exact_gamma_event_id`; event ID: `841209`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 11 | new_to_snapshot | Will Xiaomi have the best Chinese AI model at the end of October 2026? [market=3554475; condition=0xff98892eae3088f9a5a232548309ac22b84178ae000b2f14b7c144872f9a0092] | Yes=0.546, No=0.454 | new_to_snapshot | True | `1fc3573c70052854b1c6c677dfcf9aa4ccc62d25a95623c945c7fdbf7f8f6e7a` |
| context | context_unchanged | Will Moonshot have the best Chinese AI model at the end of October 2026? [market=3554472; condition=0x78c29ba8e37acdd426fb5dd351511d2f20c5cfcbe246fd1f02a5bca30d5423c2] | Yes=0.16, No=0.84 |  | True | `47c3557a974ecde95a462c6f03abc6f2540c944f2b16a5de2b986ab84f0b0fa1` |
| context | context_unchanged | Will Baidu have the best Chinese AI model at the end of October 2026? [market=3554473; condition=0x8250e15760a43b38fd2503034fc96cfceb4115215713a42bcf4d6832e1008606] | Yes=0.011, No=0.989 |  | True | `f4afa815e5d8015e2c7be54bf54154d47111e8522dc1ea35c0fb15f1328f9e98` |
| context | context_unchanged | Will Z.ai have the best Chinese AI model at the end of October 2026? [market=3554474; condition=0x64f712b42fa19413947e34fe085a4f45cfc4f4d9a0e08ea78434b3928717ef54] | Yes=0.103, No=0.897 |  | True | `ad0044fb4ff52881c58114faad6e26535fedae6350480d2e81fb6a8dd53d2aa5` |
| context | context_unchanged | Will DeepSeek have the best Chinese AI model at the end of October 2026? [market=3554476; condition=0x63f37ad0f56a63f185511e2132df1cb8094bc5bd63ea6ec640b74d47d754d722] | Yes=0.026, No=0.974 |  | True | `2abe50488707c801d377dd3eab812b6892ee94fa3db503a5d641bdc5cc3b7967` |
| context | context_unchanged | Will ByteDance have the best Chinese AI model at the end of October 2026? [market=3554477; condition=0x2403ca9b40747126a047c40e2274526777ec1decfcbec1813190df5ad21a1a55] | Yes=0.0075, No=0.9925 |  | True | `cf17b0604f052c01c1588673c91eb9542dd6c7a24c88e5f6fef2a3950c4df2bf` |
| context | context_unchanged | Will MiniMax have the best Chinese AI model at the end of October 2026? [market=3554478; condition=0xf9150bf360c2d0fa0ae497805e842265d8355861ac698619c8bed5f48cd89293] | Yes=0.041, No=0.959 |  | True | `306e54914e293fab6186c0a566ea8cefa4ef8965c8c2311068f688fc966e0ff6` |
| context | context_unchanged | Will Tencent have the best Chinese AI model at the end of October 2026? [market=3554480; condition=0xb7d5c4c9da39d867b7f76821f0565e6a45e41858953e63b1413e9bf4519355ac] | Yes=0.006, No=0.994 |  | True | `9773e2fc3c268de138cc6265e62bee57c1b6288dab09eeda4e32c37fb985eba9` |

### Ballon d'Or 2026: 2nd Place
Group basis: `exact_gamma_event_id`; event ID: `1218178`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 12 | new_to_snapshot | Will Kylian Mbappé finish 2nd in the 2026 Ballon d'Or? [market=5926152; condition=0xc09dcd5b04eef9832fc19a22ce0925bfddcd560a2aa0cf7c0a151d2aff146447] | Yes=0.555, No=0.445 | new_to_snapshot | True | `70e097869553ab5c319f7324b803d9cf1d49e9380a3573d155290b7d0844bdbe` |
| 75 | new_to_snapshot | Will Harry Kane finish 2nd in the 2026 Ballon d'Or? [market=5926150; condition=0x22df358fe89103bf01c8c09f6c328ce9b95e2deee4e01c240d9a9cbd4bb364fb] | Yes=0.135, No=0.865 | new_to_snapshot | True | `fb371cf9045d1b2bca057323aa40a66dac18165d39f56beb43243edf8ad11232` |

### Pro Football: Aaron Rodgers 2026-27 Regular Season Passing Touchdowns
Group basis: `exact_gamma_event_id`; event ID: `830673`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 13 | new_to_snapshot | Will Aaron Rodgers have 18.5+ passing touchdowns in the 2026-27 NFL regular season? [market=3503744; condition=0xdfde2fb9a94409727fb5e6744cfe59750fe75113a4751545f632a84049de7031] | Yes=0.95, No=0.05 | new_to_snapshot | True | `2c9ed5871c2d0e2bbadba6a609e11fa62e92061d509e117b775bd8c704dd1983` |

### What will S&P 500 (SPY) hit Week of October 19 2026?
Group basis: `exact_gamma_event_id`; event ID: `1202047`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 14 | new_to_snapshot | Will S&P 500 (SPY) hit (HIGH) $785 Week of October 19 2026? [market=5789113; condition=0x8c0f894a53f79f31e0be2f599f8d144a0a3dd5f42586dd77a37f3cd72996a369] | Yes=0.065, No=0.935 | new_to_snapshot | True | `05742c1c942568e27885b41801c2fe9955de76ee8bf4d87f070132cab61621d7` |
| 30 | new_to_snapshot | Will S&P 500 (SPY) hit (LOW) $760 Week of October 19 2026? [market=5789118; condition=0x1ffcd1d53d0baa6a9e08d68e6d0102c4629f98f3c6283ddb188a420c2971a512] | Yes=0.51, No=0.49 | new_to_snapshot | True | `040e5c8a9e64a57f5a34ed41c1623ae988b17dad9b738db907b6765f3fca245a` |
| 42 | new_to_snapshot | Will S&P 500 (SPY) hit (LOW) $755 Week of October 19 2026? [market=5789119; condition=0xdbe80e5bf00a037790b223bf5b327fcbee95aa2c444dd341d4d12ba9a798328b] | Yes=0.295, No=0.705 | new_to_snapshot | True | `46c5a701e3934dad9360dfab3c3625a05e5f3708f1e2eee7b696a2e6214abab2` |
| 219 | changed | Will S&P 500 (SPY) hit (HIGH) $775 Week of October 19 2026? [market=5789115; condition=0x426f04beb12c67afd83da7cb9578ccb71c820d375f923ca18cca1f8855dd8f96] | Yes=0.5, No=0.5 | best_ask, best_bid, no_price, yes_price, outcome_prices | True | `67ce9efbd98a148b4f40972547d41944da7d30f18d50d20271c1693d77d2bad0` |
| context | context_unchanged | Will S&P 500 (SPY) hit (LOW) $750 Week of October 19 2026? [market=5789120; condition=0xc618ae1f0a3729d1fad66160fd61b6fe47ac85706d2c62f7b3a55db627ccab97] | Yes=0.16, No=0.84 |  | True | `9dd9ac87d2db3c663e0afac9a1009704811041bd3ac67974dc2db1020e1667dd` |

### Will Ukraine re-enter Obratne or Temyrivka by...?
Group basis: `exact_gamma_event_id`; event ID: `257559`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 15 | new_to_snapshot | Will Ukraine re-enter Obratne or Temyrivka by December 31? [market=2374243; condition=0x3867c954ccd50c147312a14025511270bcd264b755fa40e7e3ee20df3e2c81bb] | Yes=0.38, No=0.62 | new_to_snapshot | True | `3ab1bae0c34c91b75087893a97fe92c8f013bf6926698052efb6c08c32171ab9` |

### TX-18 House Election Margin of Victory
Group basis: `exact_gamma_event_id`; event ID: `834897`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 16 | new_to_snapshot | Will the Democratic Party candidate win the 2026 TX-18 House election by 65%-70%? [market=3523968; condition=0xb4e0348d3da0c2b6f921349d22de337d16a970f8764d37ad5f5e1afe06de89ad] | Yes=0.1545, No=0.8455 | new_to_snapshot | True | `92393b71aadc09a6c020e042693e63444d70186a186db18b7ad8ba5a9a308f35` |

## Batch 4 (19 markets)

### Top 5 Most Searched Athletes on Google 2026
Group basis: `exact_gamma_event_id`; event ID: `996210`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 17 | new_to_snapshot | Will Vozinha rank in Google’s Top 5 Most Searched Athletes of 2026? [market=5605562; condition=0x99b768470913b43b509c9bb15bc78798614dfc1a52014a78d211484c4fe79f33] | Yes=0.325, No=0.675 | new_to_snapshot | True | `09c53433cb704003bd40aae8ce9ecc1ca2be6691520265db777cf7f407ef5119` |
| 229 | changed | Will Ilia Malinin rank in Google’s Top 5 Most Searched Athletes of 2026? [market=4425468; condition=0xe604ac7ffd1248b76ffbff4c49d5d8a6d891140d1881c0a21ea60ccc1fa5d68b] | Yes=0.2305, No=0.7695 | best_ask, spread | True | `bcec5b577043c0af30e06e83aaf2bd690068d21a81e3e258e774f79396d8f928` |
| context | context_unchanged | Will Alysa Liu rank in Google’s Top 5 Most Searched Athletes of 2026? [market=4425461; condition=0xa3d91e6932c60ce2d59c0f269ccc03430faa7e3080634be508e0d6a3dcccf114] | Yes=0.625, No=0.375 |  | True | `cd9fadc01eadbafb12d7f1e007a18b940f7b7f8f0a2a6717fa0a71d0d1722b28` |

### What will WTI Crude Oil (WTI) hit Week of October 19 2026?
Group basis: `exact_gamma_event_id`; event ID: `1202052`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 18 | new_to_snapshot | Will WTI Crude Oil (WTI) hit (HIGH) $100 Week of October 19 2026? [market=5789187; condition=0x2cf7fb91645b0fb16f376798e2713cdc0fab2a29cd8abe93164f5eca04da01d7] | Yes=0.795, No=0.205 | new_to_snapshot | True | `c343e7c88769000bb2143e42231d39cd9ef4287d499110bc183284cd91873921` |
| context | context_unchanged | Will WTI Crude Oil (WTI) hit (HIGH) $120 Week of October 19 2026? [market=5789183; condition=0x27c7ccb847a7aebe170863635ac96b4f90b1a6637b8669ac77cfdc7fcb99c13a] | Yes=0.0055, No=0.9945 |  | True | `c55fb9bd387846a62cbea766ffb67890b1b0a58e664db7e47bd4a1adba65cf56` |
| context | context_unchanged | Will WTI Crude Oil (WTI) hit (HIGH) $110 Week of October 19 2026? [market=5789185; condition=0x71b7432d193dbf02d2e15da870c3a1edad23162a8e7244a7eb324f22ec6c9422] | Yes=0.063, No=0.937 |  | True | `57cc9c2452bd1562d7b645edb28e7384ce940b736747e70a26ce7a3cb5d6260e` |
| context | context_unchanged | Will WTI Crude Oil (WTI) hit (HIGH) $105 Week of October 19 2026? [market=5789186; condition=0xe3b968b4a8a47465d812a0e70630d1ad83b284d199293a8b9bc0f45ddcfe8e5d] | Yes=0.225, No=0.775 |  | True | `c587825a6ad7942103c4eed6a96f052ad1d52e0a9171834b44dcab0c2cafcba6` |
| context | context_unchanged | Will WTI Crude Oil (WTI) hit (LOW) $95 Week of October 19 2026? [market=5789188; condition=0x2ca5b78b051474f62cbb734987bb6dad3cd3231f11f784ed094aeb912c008702] | Yes=0.45, No=0.55 |  | True | `ba0e0047a89b1954233e6def3a78c157da66d2566dbf39dc327a4aff8847a215` |
| context | context_unchanged | Will WTI Crude Oil (WTI) hit (LOW) $90 Week of October 19 2026? [market=5789189; condition=0x5067035c913ae5555102693516eca9450ef5aba11009cd04a9b1e62e71ebae66] | Yes=0.1, No=0.9 |  | True | `baf456c36576db32468cd505dbbaf2a54309b695f46fa3d914170694ceeaad05` |

### Donald Trump # Truth Social posts October 16 - October 23, 2026?
Group basis: `exact_gamma_event_id`; event ID: `1180834`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 19 | new_to_snapshot | Will Donald Trump post 80-99 Truth Social posts from October 16 to October 23, 2026? [market=5640243; condition=0x8d8bd528828480749b7ae233173cd75ce4d63396728bca00c9dcdabf5b6690a9] | Yes=0.1045, No=0.8955 | new_to_snapshot | True | `503e2698dd5e656e5b49e0cd5dca76ad1c757456b29a000676f86e0e3d7b89e3` |
| 188 | new_to_snapshot | Will Donald Trump post 160-179 Truth Social posts from October 16 to October 23, 2026? [market=5640284; condition=0xc9406f19ce32b9521c7a3784cf41406c5e2ccd8f32a0620482fe8a8f73e7ed9f] | Yes=0.118, No=0.882 | new_to_snapshot | True | `41951c957265c1a2808afe70ea83bc43028d03f69bb58c69d02fc0b4b3970ead` |
| context | context_unchanged | Will Donald Trump post 100-119 Truth Social posts from October 16 to October 23, 2026? [market=5640252; condition=0xa2b5e25232d0860b10b353f852e01f18969da559f92661bf248f4bd124389604] | Yes=0.2695, No=0.7305 |  | True | `389f1acb671bed80d7986eabd9a9e1bfd318457419ef978d2da027c28ad16284` |
| context | context_unchanged | Will Donald Trump post 120-139 Truth Social posts from October 16 to October 23, 2026? [market=5640263; condition=0xfdfd375cad0d888ffb7739b6eacf8b1358962eb6bc71c154276a4882a4f5e55b] | Yes=0.2495, No=0.7505 |  | True | `0ae5a965e21cc64f37fbc1b100c9625052aa39ce535c934aed5a49e8874db378` |
| context | context_unchanged | Will Donald Trump post 140-159 Truth Social posts from October 16 to October 23, 2026? [market=5640270; condition=0x0321fe9e2e3fc04a57f2fdc3c950796c958575c2a6af879954bc80f744b329c0] | Yes=0.149, No=0.851 |  | True | `0472f13d241436b1157b95fc1c21ae09a22436c0791147a8bb99251a60d52bb7` |
| context | context_unchanged | Will Donald Trump post 180-199 Truth Social posts from October 16 to October 23, 2026? [market=5640297; condition=0x960cd46bc82729fc9804ef2ee33df33a4e424297b1951609da934f818da2f764] | Yes=0.0455, No=0.9545 |  | True | `e5374539f66a811e906a21ee46ee4b74dcaca9ad4be947facebc7a05b3b4f38e` |
| context | context_unchanged | Will Donald Trump post 200+ Truth Social posts from October 16 to October 23, 2026? [market=5640308; condition=0xcc393553caf07818a6352256a89471ef0097fb7b67026072f1fac81eddec8368] | Yes=0.067, No=0.933 |  | True | `d786fff6e8c7df7c4f7739ece013f7e287dbf79d074cefc40d8651d1eb4cd40e` |

### What will South Korea ETF (EWY) hit in October 2026?
Group basis: `exact_gamma_event_id`; event ID: `1078051`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 20 | new_to_snapshot | Will South Korea ETF (EWY) hit (LOW) $140 in October? [market=5824844; condition=0x7b6824722d15b5d3f9589cfd13947ec704d297a662425c660f495126dc119542] | Yes=0.21, No=0.79 | new_to_snapshot | True | `b24fab38abc09eda2e0aa598ffac31136b170bc215c355eb16648b7cec226957` |
| 67 | new_to_snapshot | Will South Korea ETF (EWY) hit (LOW) $144 in October? [market=5778286; condition=0x6f4ed39fcab59457497790559fe76580a2c131efdf2512bd751ef8f6bad616f2] | Yes=0.31, No=0.69 | new_to_snapshot | True | `75f676137a837546ec6697fbd6e9cafd7e61f9a03243d53a3993ba336dd1cd28` |
| 101 | new_to_snapshot | Will South Korea ETF (EWY) hit (LOW) $138 in October? [market=5824845; condition=0xf421e0d99ab9c3b4a9a131c9ffc7b392d14612d1ad043d53159ddcb296a822a9] | Yes=0.18, No=0.82 | new_to_snapshot | True | `ba42aa81e29e8458a6d6d8493a9961fb0669946987a9c0fe97a50d0de20a04bb` |

## Batch 5 (18 markets)

### StandX FDV above ___ one day after launch?
Group basis: `exact_gamma_event_id`; event ID: `78999`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 21 | new_to_snapshot | StandX FDV above $1B one day after launch? [market=676518; condition=0x31f521ffcf9b23c876d418bbe8205ac1fab62d0aed60d6dbbc66ca3b01bdbff5] | Yes=0.033, No=0.967 | new_to_snapshot | True | `beecc23835de4dcc1bf087b6fc8f147b1631f3a49369ad52b1176d8cd20e9996` |
| context | context_unchanged | StandX FDV above $400M one day after launch? [market=1299974; condition=0x3de44d7bad27379abaebb57485589cbb2a309aba16219bcbe182124acdf70800] | Yes=0.0205, No=0.9795 |  | True | `8d2235d4eac056062d1242523f28dbfbc7fb6b1b95ff22124306c3e2e04ec8b7` |
| context | context_unchanged | StandX FDV above $200M one day after launch? [market=1370033; condition=0x45a913e982a9e299b3b4e7473bce2c256c8c2a90f4bbefe1c5b8532ef89efe33] | Yes=0.0145, No=0.9855 |  | True | `f2af7fb0e45a0ddab88151341aec06840ca74c930ac6dfafa615450c421e21c3` |
| context | context_unchanged | StandX FDV above $50M one day after launch? [market=2831225; condition=0x65e4f39d20808d2f146177dcea037c9a01198ef2680793221fd18a0118542f48] | Yes=0.0085, No=0.9915 |  | True | `d2cadf8b704d0155d2e3fd18fe4d2636ce24c1da4286863824164486f0dae38a` |
| context | context_unchanged | StandX FDV above $100M one day after launch? [market=2831226; condition=0xbe8f86c8cd53038dd14685177b049d9ff557104ba857e94643cf2853a95c9d87] | Yes=0.0075, No=0.9925 |  | True | `3a3a6c0cfaf3df0ddee287b2964c1ac7012d07ca9e529b8b52a2bf5724f80df9` |
| context | context_unchanged | StandX FDV above $800M one day after launch? [market=676517; condition=0x98a00a768588cb4ea560143e9a4140428102c3b82e9dad2972329fc6806d36c9] | Yes=0.014, No=0.986 |  | True | `4639917c635c4b7308380b7c47e8d0f2d7aa219dd1b3a4fc3b6151a51b974c70` |
| context | context_unchanged | StandX FDV above $3B one day after launch? [market=676520; condition=0xf411b549a0f6dbdd7cf1386adca51ea2043674fbf6b18a9137787e7ebb3e2146] | Yes=0.023, No=0.977 |  | True | `ceb07c1efb64e2d4d0ae5a174555ed26381a63ee2f9586464a64adc653aa30a5` |

### Republican Senate odds hit __ by October 31?
Group basis: `exact_gamma_event_id`; event ID: `1061741`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 22 | new_to_snapshot | Republican Senate odds hit 40% by October 31? [market=4826274; condition=0xebce4765f5ca728d432ea4ee04020c79d09c055c8004fcbcaf787242324a2760] | Yes=0.395, No=0.605 | new_to_snapshot | True | `66f5b43aaf0af2d7c8166fc98a3df14bce4da5cf3d63d53a783dc9ffb6fda09a` |
| context | context_unchanged | Republican Senate odds hit 45% by October 31? [market=4826275; condition=0xe95f14e0db9837856e3c8c01e9a191e81e0327839df77ef012569d14ed8664c4] | Yes=0.105, No=0.895 |  | True | `e78d3de1d97905c7479fa627b758ef99d7e91b96659bd0b908f1ddfa36416adb` |
| context | context_unchanged | Republican Senate odds hit 50% by October 31? [market=4826276; condition=0x9aa0e3486e5c7d46d29d1dae13b185b8961bd955465db4632ba8a28803939dca] | Yes=0.0015, No=0.9985 |  | True | `a4d3d9bcb36c3004083a306d5cfa83eb1a54d7e41d4fe72c943238683a6ed733` |
| context | context_unchanged | Republican Senate odds hit 55% by October 31? [market=4844536; condition=0x4ab25b3263eac3c96501205489d1d439abb300be30e5d47af694076d50a37b3d] | Yes=0.011, No=0.989 |  | True | `831a1d8adbd62bd2be5e5bb27f95edd31ccf43804bc2116a19912a9b1186cf73` |
| context | context_unchanged | Republican Senate odds dip to 30% by October 31? [market=4844538; condition=0xfbe29d06a6d9180b8d26d053680cae3b180801add24e64971e12b1f7455b4c7e] | Yes=0.185, No=0.815 |  | True | `96ccc5665a714a41bc0ec62f9e24d99ef3b7b090382f397be9f96e51c9cb8a4b` |
| context | context_unchanged | Republican Senate odds dip to 25% by October 31? [market=4844539; condition=0xc16f746af08ef316bbf2ec666447e03357b31d82b8f5d2df7fbe41e3a639b686] | Yes=0.065, No=0.935 |  | True | `58e30507f68c77f0588b78c65b2127df22a1398d8d04f6e876be9324e19e27cc` |

### Oscars 2027: Best Original Score Nominations
Group basis: `exact_gamma_event_id`; event ID: `1188319`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 23 | new_to_snapshot | Will "Dune: Part Three" be nominated for Best Original Score at the 99th Academy Awards? [market=5686355; condition=0x9b2244b5a3a83b84a24d3fced02dc64c5ec042db30d7ce8460210b29a6a6c642] | Yes=0.685, No=0.315 | new_to_snapshot | True | `747994199e5c8d4a013d978c724ef43c0cb1ac9bdca4615386257bf27a61fa22` |
| context | context_unchanged | Will "Behemoth!" be nominated for Best Original Score at the 99th Academy Awards? [market=5686361; condition=0x75faf2a1c5ef078b3918cd4d38b98a4ca36a3978d9af96fb2e6497c1e48ff10a] | Yes=0.365, No=0.635 |  | True | `2cedde2edb0232e1c83d788f6b6d494155bef1342265e09ad7ec32bd3ca7a904` |
| context | context_unchanged | Will "Project Hail Mary" be nominated for Best Original Score at the 99th Academy Awards? [market=5686364; condition=0x4cf0e7a5f281267f62cec68b0c547453f9229decd53b873863af188b251e3b7d] | Yes=0.595, No=0.405 |  | True | `c034c0980c862c5c1f3fba3712bab458df5cc763b0ccdd49d55b57516e1d616b` |
| context | context_unchanged | Will "The Further Mis-Adventures of Cliff Booth" be nominated for Best Original Score at the 99th Academy Awards? [market=5686366; condition=0x5620bde4d7b7940e2977fd950d8ce4feb8b8bf4f27cc774fc3cdd5b54e2dc14f] | Yes=0.115, No=0.885 |  | True | `277d996daedf7b96d152197270ce854d1ef4262c0fb01358b3d216a9ac2f1da3` |
| context | context_unchanged | Will "Whalefall" be nominated for Best Original Score at the 99th Academy Awards? [market=5686371; condition=0x8b5221be9f4d7abfef0b23d66273ff81b218b5f41d069a6b0c92f2bf2151bd5f] | Yes=0.032, No=0.968 |  | True | `2deb47c322a6a2db60b218b7dee2fd01c02043fd13c2f64bfd9feed918251c96` |

## Batch 6 (19 markets)

### Who will attend the 2026 Ballon d'Or ceremony?
Group basis: `exact_gamma_event_id`; event ID: `1200407`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 24 | new_to_snapshot | Will Michael Owen attend the 2026 Ballon d'Or ceremony? [market=5780993; condition=0x7a9b9fc81b9945c6adcf6f3d731627823aa96281096533e7b40ed6d86844637b] | Yes=0.705, No=0.295 | new_to_snapshot | True | `2d4622b7bbead7a3bf099cea1534d8e9698012266e5a74a48de0c4279ec64853` |
| context | context_unchanged | Will Lionel Messi attend the 2026 Ballon d'Or ceremony? [market=5777942; condition=0x61cd94712a574f61c80b66f94bf674abf620398fba0e8b6fc742d00f85601f2c] | Yes=0.465, No=0.535 |  | True | `aa704a3cc07c225ecf1f4e826add626b50d9595ac070d68584883bd64d791eb4` |
| context | context_unchanged | Will Lamine Yamal attend the 2026 Ballon d'Or ceremony? [market=5777944; condition=0x21cbd4ad20b4d2781c6050c3a8cd8accbe86ea80275786d4ce9131e52c7b78c7] | Yes=0.9455, No=0.0545 |  | True | `21b4a78d5bccca217ca94473409c84cf7e71763ea5108c1df5d26a52b189db0f` |
| context | context_unchanged | Will Kylian Mbappé attend the 2026 Ballon d'Or ceremony? [market=5777945; condition=0x82bd18b880ec8865a7f86f44867e7978038612192bedde90f4753d7a183de181] | Yes=0.75, No=0.25 |  | True | `e12c623ca31a9c7202c9ce20dceed6fec5d0c090875bf423363785e1f91a333a` |
| context | context_unchanged | Will Harry Kane attend the 2026 Ballon d'Or ceremony? [market=5777946; condition=0xeab90e298d2c74335867f2e764d5975939cd64183189227c3494f6eda82deb4a] | Yes=0.9745, No=0.0255 |  | True | `0d699a81c428b4ec8e9279b09092e05ed30d03ec055d38d9776657d09faefabd` |
| context | context_unchanged | Will Ousmane Dembélé attend the 2026 Ballon d'Or ceremony? [market=5777947; condition=0xdad9ceaa5be49f625f6da66d2a5656f6133474ef3e180f433960b63de5e7b1e1] | Yes=0.9675, No=0.0325 |  | True | `0a4918f05ac1e08751f185f34dc9116c4a774798da6e6adbb5a088e8dc59a830` |
| context | context_unchanged | Will Rodri attend the 2026 Ballon d'Or ceremony? [market=5777949; condition=0xae92666c5603b859294f21a999ef3b4fd2a6c25a28d7cf792e9ad19be5798e00] | Yes=0.96, No=0.04 |  | True | `a41f6309119b33d7562dc2b1a3a7fcf01cbcded3b241faa587a4babbe71c1ca8` |
| context | context_unchanged | Will Zinedine Zidane attend the 2026 Ballon d'Or ceremony? [market=5780988; condition=0x1925639f313a4705c288835147090e4f8cebc8b2988acf49ce9b653aa9645115] | Yes=0.325, No=0.675 |  | True | `a6983a88d0085b17e9ad9549504b4995d7926e32c16532c64f5e919946a87b03` |
| context | context_unchanged | Will Sergio Ramos attend the 2026 Ballon d'Or ceremony? [market=5780989; condition=0xd91c4cd7ebac5effee9ad35e2d62ec81bc15b5bbfb0be159e2d056a2636df867] | Yes=0.265, No=0.735 |  | True | `be18e5d9a11f80f1400084da6320374e1bbd9e507e0a26758c900c3aaec6e0ac` |
| context | context_unchanged | Will Xavi Hernandez attend the 2026 Ballon d'Or ceremony? [market=5780991; condition=0xc503d89bf0a0320189d33970d9ff10ee9ae73faa4eceeeafd2cbdd76a860cf4d] | Yes=0.285, No=0.715 |  | True | `964d9ef125b5752694bb82e8fd0eba40e93391c1c7cf6e58070f8ec3eebc6769` |
| context | context_unchanged | Will David Beckham attend the 2026 Ballon d'Or ceremony? [market=5780992; condition=0x8369878dee4427dcc0ab6cb20794084defbb86149c4c5377057f5126829385d7] | Yes=0.77, No=0.23 |  | True | `2eb2c6909b9355c2afd3eb2bfe130eddb2b6ea65a8d294d3f0fbc4a01114ee15` |

### What will Apple (AAPL) hit in October 2026?
Group basis: `exact_gamma_event_id`; event ID: `1078020`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 25 | new_to_snapshot | Will Apple (AAPL) hit (HIGH) $352 in October? [market=4935699; condition=0x9cfe773ea6105ce756d5113c8365997b5ac4063770b15568f07a0d3fa2484fc8] | Yes=0.47, No=0.53 | new_to_snapshot | True | `03f5a486318d6959172305a1dcef993449e2450ec47805485110ff3493fb8c4a` |
| 159 | new_to_snapshot | Will Apple (AAPL) hit (LOW) $320 in October? [market=4935708; condition=0x2a28151fcc951fe188ca0f460a328d4b8d25e6241a429852ad5bb36bae8e4935] | Yes=0.135, No=0.865 | new_to_snapshot | True | `d5dbf868bf54b65071bd7877fb22ce0d2396d8418fa40c1f794fe646c98e3841` |

### What will Apple (AAPL) hit Week of October 19 2026?
Group basis: `exact_gamma_event_id`; event ID: `1201999`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 26 | new_to_snapshot | Will Apple (AAPL) hit (HIGH) $356 Week of October 19 2026? [market=5788580; condition=0x172f995784ed34983002a90c4f5864cdeb1a00954a6ab87d3ce4abe94d6cb320] | Yes=0.18, No=0.82 | new_to_snapshot | True | `b918cdc44a3c0af6d9c9e68906d9557c2a98a8eaa0cb706a497f1441817aa62c` |
| 124 | new_to_snapshot | Will Apple (AAPL) hit (LOW) $336 Week of October 19 2026? [market=5788595; condition=0x45f53262f79254856d1b42fdbbc80da306f6a47423f61d21978d3e8640f5ad7c] | Yes=0.535, No=0.465 | new_to_snapshot | True | `79ac4265df62eb7caa6627e589647f9795f05206c17d949851b1024baec87647` |
| 185 | new_to_snapshot | Will Apple (AAPL) hit (LOW) $324 Week of October 19 2026? [market=5788602; condition=0x1242ef46cb30a4ba97b76d1281fa822c56c666062a12880cbaa3db7f81c5717d] | Yes=0.095, No=0.905 | new_to_snapshot | True | `94148ace02a3c5aabfc37e06e58c56bc9f1e756dab14d0fd7dc2370c4dfba7df` |
| context | context_unchanged | Will Apple (AAPL) hit (HIGH) $352 Week of October 19 2026? [market=5788583; condition=0x48952dfa6337eee33688a78721640f9244751518c9845052c604ab58f8c9a095] | Yes=0.3, No=0.7 |  | True | `0c86be739684c0d6a5c30ed7e1c35484df23ab4a4d59452c25bb363ec8c0ade8` |
| context | context_unchanged | Will Apple (AAPL) hit (HIGH) $348 Week of October 19 2026? [market=5788586; condition=0xf4621af1efd80e16e67143aefa2f6ae126a78f30018e97fe25bce4f0f9e1363b] | Yes=0.53, No=0.47 |  | True | `575d1c304c8d8867a4ff5f5e0fd42eb93827d4836c5afd48656dfe4b0e4e1b44` |
| context | context_unchanged | Will Apple (AAPL) hit (LOW) $328 Week of October 19 2026? [market=5788600; condition=0xf8164d3e9b9ef03a4119046cfb03554db6ba9ce8b7bcf0e20201858c71eaca1a] | Yes=0.195, No=0.805 |  | True | `e667240896680746733275e180578998b511e0606be4e0dfdc2cda922f3678a9` |

## Batch 7 (13 markets)

### New South Wales Parliamentary Election: 3rd Place
Group basis: `exact_gamma_event_id`; event ID: `1159353`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 27 | new_to_snapshot | Will Liberal–National win the third-most seats in the next New South Wales state election? [market=5457458; condition=0x2be7db5fc6f7289ae57e63777d1a07f22e30d6a35940b1798ea163019b5bc078] | Yes=0.135, No=0.865 | new_to_snapshot | True | `08b2b8cd7649c3e70eee8973e47ddaa04102f03f43b394472d9ef9b7c03fd008` |
| context | context_unchanged | Will One Nation win the third-most seats in the next New South Wales state election? [market=5457460; condition=0xe3b52c31f596e8551a481be8214c6fe27e0cf6478137b21fa054808f8ad2a9a7] | Yes=0.415, No=0.585 |  | True | `21db36458177d8642d1f017c49767efce79ae9ef60ee0eab0d777d489f3572f6` |

### ISM Services PMI - October 2026
Group basis: `exact_gamma_event_id`; event ID: `1141227`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 28 | new_to_snapshot | Will ISM Services PMI be between 52.0 and 52.9 in October? [market=5364738; condition=0xe80effc1c1921b840f6017e8eb03c8a8ba1852d5c9a7862351062674711511da] | Yes=0.114, No=0.886 | new_to_snapshot | True | `726e13cae1ed96b48926a149f90823593ec8fccbe8c30197058eff4a2977d97f` |
| 127 | new_to_snapshot | Will ISM Services PMI be between 53.0 and 53.9 in October? [market=5364739; condition=0xebf06c587a50c7b928026d0b9d4770c82a7789ca15d271d1d7c3566d616a1189] | Yes=0.345, No=0.655 | new_to_snapshot | True | `55184eb73a95c353ef250d4425f0e495671a3352a614504ac5e8849ccd19085e` |

### Pro Football: Panthers 2026 Win Total
Group basis: `exact_gamma_event_id`; event ID: `912348`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 29 | new_to_snapshot | Will the Carolina Panthers have more than 7.5 wins during the 2026 NFL season? [market=3887332; condition=0x509e4e02ffb0a6e6ca553fd16921bb2c710f303f16edb88c3d5638179f5e3e6c] | Yes=0.68, No=0.32 | new_to_snapshot | True | `0ded14ba1c15742c5a8fe08634c554fcd3f1543333928fbd28dc529d25812f80` |
| context | context_unchanged | Will the Carolina Panthers have more than 5.5 wins during the 2026 NFL season? [market=3887330; condition=0x042bab1a495cfa81531844beb48ff1ee95c98cf1fac9c6db3c84609a1cb1b852] | Yes=0.89, No=0.11 |  | True | `3ef67100d92dbb0acca0fe38d016ec81fe7d654ed6dcdbc0f6c89c9e1ee2d78c` |

### Alaska Senate Election: Turnout (First Round)
Group basis: `exact_gamma_event_id`; event ID: `870851`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 31 | new_to_snapshot | Will total votes cast in the 2026 midterm election for Senator from Alaska be between 275,000 and 290,000? [market=3697436; condition=0xc00c0836939fd6aee6b4628ac854b1b3dba7a71f1f20211d16e378b6a401b4e3] | Yes=0.26, No=0.74 | new_to_snapshot | True | `6612cb6215c0b53be3c9c2c6be9ff5d0d6e84ed636814f8f9ef7e0eeee573bdb` |
| context | context_unchanged | Will total votes cast in the 2026 midterm election for Senator from Alaska be less than 230,000? [market=3697432; condition=0xade7890cf51e2bfec343689a5c40e0a5953057c6501b2ff2fd776b31eb4ce7ff] | Yes=0.0025, No=0.9975 |  | True | `9ae8db31273e2b7d613cfc64ccb677a4a9fbd5f671b60068b81669c1c67a47d8` |
| context | context_unchanged | Will total votes cast in the 2026 midterm election for Senator from Alaska be between 230,000 and 245,000? [market=3697433; condition=0xa64ad965ff5aca780cd651b657b4723a6ac7b6c18b56b2e474b1f250486245d5] | Yes=0.0045, No=0.9955 |  | True | `3f90f16b619caa32b136002d102ca5c42257cff8a2ad2ed4c5c1ed6ec5f2353a` |
| context | context_unchanged | Will total votes cast in the 2026 midterm election for Senator from Alaska be between 245,000 and 260,000? [market=3697434; condition=0xff1175de33244dd027ef992e269c774d03b93485e3149e8cdee8a85db65c4deb] | Yes=0.0035, No=0.9965 |  | True | `0884dad588fba65a001ea720078c8af24ffe952152a30753cfa48fa49612b66a` |
| context | context_unchanged | Will total votes cast in the 2026 midterm election for Senator from Alaska be between 290,000 and 305,000? [market=3697437; condition=0x62b8efb4db753aa64cd337c425f2e58c82cbcff42603689da0792e68c8c04d01] | Yes=0.32, No=0.68 |  | True | `b6443fc53589adc11c6ab4c5adfc0d176c9ca342781a9b0861aeb62ef0502f30` |
| context | context_unchanged | Will total votes cast in the 2026 midterm election for Senator from Alaska be between 305,000 and 320,000? [market=3697438; condition=0x299ebe6d77f5aece068d9838192f1955b9c587b12d4a1271c7a4f033eadcb182] | Yes=0.23, No=0.77 |  | True | `9d6e3a4492277c67752b98495d33158d25c2d825a71e276e79bce4136fcbf914` |
| context | context_unchanged | Will total votes cast in the 2026 midterm election for Senator from Alaska be 320,000 or more? [market=3697439; condition=0xbf3c2dd58813c84ccf605ec335cab82a9825b948d61a7d3a5aa55ff4daaf7222] | Yes=0.1075, No=0.8925 |  | True | `23fc9d68216176d64aa77bf9679cc1c13b925bb27de55e8e1842a3a3676f332a` |

## Batch 8 (20 markets)

### What will Silver (XAGUSD) hit in October 2026?
Group basis: `exact_gamma_event_id`; event ID: `1078054`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 32 | new_to_snapshot | Will Silver (XAGUSD) hit (HIGH) $62 in October? [market=5331385; condition=0x7f5a5814f1a4ab1d8138294d7f5094b5fd4e9520f70186ed6fbaafc05b78c2d4] | Yes=0.205, No=0.795 | new_to_snapshot | True | `9ee383fb8524f7961330f67fa94ae0af8b61b2e721358fc6f0839f94cbbcf830` |
| 230 | changed | Will Silver (XAGUSD) hit (HIGH) $64 in October? [market=4936090; condition=0x3056265c711574f43ecb11788c27fa2b2557ec8990cd1217e9935ffd50bffbc5] | Yes=0.1125, No=0.8875 | best_bid | True | `75743d237163b354f90039475d33ed4ffd0042a26cf679adf777714ebf8836ff` |
| context | context_unchanged | Will Silver (XAGUSD) hit (HIGH) $74 in October? [market=4936085; condition=0x76180ba4577e4c780a495795adf8e1adc20655ccfc629e15e9ad27aab29dc063] | Yes=0.0065, No=0.9935 |  | True | `90ba9a71b50facdb5cb5aa790d6f1e1e81bd48cf3230afe378b109f31ff879cc` |
| context | context_unchanged | Will Silver (XAGUSD) hit (HIGH) $72 in October? [market=4936086; condition=0x0209bdb181dd0983537e923ef3d4d970339a330548a97a62d6f6b6850be729d5] | Yes=0.0085, No=0.9915 |  | True | `b3387ae178283dc53aed5429aa9ac8658a733c8414a3fd51d0ee2ca775676243` |
| context | context_unchanged | Will Silver (XAGUSD) hit (HIGH) $70 in October? [market=4936087; condition=0x08694b476d9ad72a1875b32a1fc2423b36bb7d38b7b158b1b4fd03f951a3a9e5] | Yes=0.0185, No=0.9815 |  | True | `83dbf9d52799f9f377c841c2bc7cd59be5b5cd75ac1d781b8259dfc33c28ebd7` |
| context | context_unchanged | Will Silver (XAGUSD) hit (HIGH) $68 in October? [market=4936088; condition=0xf7c06cc692f2409ff7210635d7a0ae1ee548c5a3894b9abe290f242ea1910994] | Yes=0.0145, No=0.9855 |  | True | `a80a51a49a4e28713315b61e212810d0d9f519f41bab6ca6c06c16b576815882` |
| context | context_unchanged | Will Silver (XAGUSD) hit (HIGH) $66 in October? [market=4936089; condition=0xc52dc14bcf7e33a422a4d98f1ecc9cbdf1f8d2c375402b998e0d0d35864715fb] | Yes=0.045, No=0.955 |  | True | `297ce988e0e717e7d9fa4db1357a7337177b45d871b60d336d73120d77867a6e` |
| context | context_unchanged | Will Silver (XAGUSD) hit (LOW) $54 in October? [market=4936095; condition=0xafa123bb52cf24e23b099d9d63e584ee44cecf97d7b31175748a57719915b5c5] | Yes=0.355, No=0.645 |  | True | `160004e2458404265f66909f687c9637b61e7a68b591c588ebf5e5292704a0ef` |
| context | context_unchanged | Will Silver (XAGUSD) hit (LOW) $52 in October? [market=4936096; condition=0x52a2862d94facd550f0be361c6f52b102ea1223c7d8d90112152c2df7ac14397] | Yes=0.135, No=0.865 |  | True | `4c6dd8fb7e00f62172079e69546534c092821582da5876a93f2cbe58cdceb012` |
| context | context_unchanged | Will Silver (XAGUSD) hit (LOW) $50 in October? [market=4936097; condition=0x78840f4feb990a2d8100596824d82e7f7aa46bb7aff1994b8a008201c6da8108] | Yes=0.0695, No=0.9305 |  | True | `ccb75f75243d7d51772c1fa8a93bf59e722bf9cbf767a042c857290e07dc0f29` |
| context | context_unchanged | Will Silver (XAGUSD) hit (LOW) $48 in October? [market=5208214; condition=0x0964e7eb04ae6c4f5064d44bfb7e4acd35ef747fb54fbf2a5a9e7d9d6db24d48] | Yes=0.021, No=0.979 |  | True | `b0be2f7b6973864fa37077970800487c6e7274d7161dbe29b20eb0915618900e` |
| context | context_unchanged | Will Silver (XAGUSD) hit (HIGH) $58 in October? [market=5691733; condition=0xcddf5ee283ebb56806f8ad0e6a210271e9440ecf5db3c5bb0b6fe79a7bc840a9] | Yes=0.829, No=0.171 |  | True | `9daa5d9d364ba8c8d4ae6843958a02b3cb67c956d6bb590879aac41ba7c8ab08` |
| context | context_unchanged | Will Silver (XAGUSD) hit (LOW) $46 in October? [market=5691737; condition=0x947041d514a6db1ac794a4fdd432a839bd022c2ad06faa54ebee5bfa52ce81d0] | Yes=0.005, No=0.995 |  | True | `d36074c61ab8d6ba2c43ed2f51d4cb3367072e5b997282208bcb7b563e516d0e` |

### Who will Trump pardon before 2027?
Group basis: `exact_gamma_event_id`; event ID: `83804`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 33 | new_to_snapshot | Will Trump pardon Himself before 2027? [market=687675; condition=0x6bc658b5fdfded234356308d971d7b93e2e92c48eff32144bc163b4a3da7277b] | Yes=0.0505, No=0.9495 | new_to_snapshot | True | `66afd511dda2e991e352cae20bfa1b396f7297719612908061aaeb1263450126` |
| context | context_unchanged | Will Trump pardon Steve Bannon before 2027? [market=687672; condition=0x4a869db910b4f8e3dc8e4b562889939b2ad272c8cef5914eadeb12fb6b979ad2] | Yes=0.092, No=0.908 |  | True | `1c6e2755a90adaef9f3e4cc4155649da46692801f481b9577edb915af9d12f10` |
| context | context_unchanged | Will Trump pardon Stefan Brodie before 2027? [market=691634; condition=0xa5037368e1c68fe7efb9361b57e5c010e701ff0bc6ee41fd7a98bc8f8cf866b1] | Yes=0.155, No=0.845 |  | True | `cd2cbdcd42b3e8f4746df4f638ffad6bb5668c6d8b3e350ced7b26e1e7d3f712` |
| context | context_unchanged | Will Trump pardon Ryan Salame before 2027? [market=822866; condition=0xbde10fc985687f35034b62df6cd50adbe835dcf08a36a93c4c695ed75777e32c] | Yes=0.12, No=0.88 |  | True | `3afad0ff440c2167f36e703ab54094cb50dd38f04257cdf9f2b8345ea7c6bffa` |
| context | context_unchanged | Will Trump pardon Keonne Rodriguez before 2027? [market=951551; condition=0x54701be7ec2f8ae91308ef7ca1e28720f74664e3d3dc446ceef76e86a785e579] | Yes=0.1, No=0.9 |  | True | `9402b7d3acb42747153410b42e50401c8659bbaeade077a234c08801bee8af64` |

### Israel Election: Yisrael Beiteinu vote share?
Group basis: `exact_gamma_event_id`; event ID: `989696`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 34 | new_to_snapshot | Will Yisrael Beiteinu win less than 5% of the vote in the 2026 Knesset elections? [market=4375452; condition=0xca272965873a68c5f6e2cd81240a990d3080268f3a8cfd907e8b1126dd2c482c] | Yes=0.145, No=0.855 | new_to_snapshot | True | `a876c98c625c5fc221a207260be3db03eb3e3a4142b9f289efaafecf32fd74c9` |
| 248 | changed | Will Yisrael Beiteinu win 7-8% of the vote in the 2026 Knesset elections? [market=4375455; condition=0x34323599e17a3b7cd270307f68e47251f22e6ad78ba0634b1bacaa625fae0be7] | Yes=0.22, No=0.78 | best_bid, spread | True | `41ab6b75b5c746c4654c3de0dc8bed2d5b04cb4c54bc308bbb182c96f1dfdec5` |

## Batch 9 (20 markets)

### Tennessee Senate Election: Turnout
Group basis: `exact_gamma_event_id`; event ID: `870885`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 35 | new_to_snapshot | Will total votes cast in the 2026 midterm election for Senator from Tennessee be between 1,800,000 and 2,000,000? [market=3697626; condition=0x999ac607199ef9ddb64a8544186b52022fd8e6ab01b5f7e0496f4adac7cb00b4] | Yes=0.25, No=0.75 | new_to_snapshot | True | `d85135eb388223decc3aca98b8d046cc8d49511da84385afef826a467f24d91c` |

### How many tropical cyclones will make landfall in China during 2026?
Group basis: `exact_gamma_event_id`; event ID: `802314`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 36 | new_to_snapshot | Will more than 8 tropical cyclones make landfall in China during 2026? [market=3365665; condition=0xa37160b65b9182d309f196d61f86cdb67580a0b9a1f5438afbc5b23fd6d36808] | Yes=0.655, No=0.345 | new_to_snapshot | True | `c72da052e7e895b06f2b772f9a540b5a6d5c6f1e1b77c3ce4a64a3b60ff4c539` |
| context | context_unchanged | Will exactly 7 tropical cyclones make landfall in China during 2026? [market=3365663; condition=0x515c13a79190731d353f97ecadf808cfdf7eab93f3d4b2583a3eab2558f21e3f] | Yes=0.0345, No=0.9655 |  | True | `7b3d3e1f345bd04e31cd21a0fe5ab8de4b31aba56831c73f80cecd4a378b24f2` |

### What will S&P 500 (SPY) hit in October 2026?
Group basis: `exact_gamma_event_id`; event ID: `1078050`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 37 | new_to_snapshot | Will S&P 500 (SPY) hit (HIGH) $780 in October? [market=5407814; condition=0xe45ba2c8b4d15f248438665080c6ecdf6837efef7457dd0ccbfbef535fed7b5a] | Yes=0.504, No=0.496 | new_to_snapshot | True | `2b7814a4aaefcae81e11d09289ff47ae39743362fb7bb354cc858a7cb562d33b` |
| 59 | new_to_snapshot | Will S&P 500 (SPY) hit (LOW) $760 in October? [market=5181352; condition=0x7273dfbbea0e3be2643df2c8c8e223fa6f816635711e5728d3de70f3cd96cfd5] | Yes=0.689, No=0.311 | new_to_snapshot | True | `60a9470563082de24857bad8c9938454c09f615eaf81383ca4a5ff88c9a94b06` |
| 206 | changed | Will S&P 500 (SPY) hit (LOW) $750 in October? [market=4936036; condition=0xdb513228f83aa65b7a12ddd5425479d0ee2501312f6f9e5dfe1c938aa1ea2865] | Yes=0.35, No=0.65 | best_ask, best_bid, no_price, yes_price, outcome_prices | True | `446aa16d79868a869a64b4c05aeac4090546850871edf2cb4771d0037b443c11` |
| context | context_unchanged | Will S&P 500 (SPY) hit (HIGH) $800 in October? [market=4936031; condition=0x1f5706ead238dc4d97ba364a918221aa9c7d3866e6696a12bbb1266f953527d9] | Yes=0.0735, No=0.9265 |  | True | `7a21972c4196576c8e98b430a48975405256f2875e0ada3bc100b90ef907212f` |
| context | context_unchanged | Will S&P 500 (SPY) hit (HIGH) $790 in October? [market=4936032; condition=0x0cb89595e95d7a887b50855c5f3a4fa1b40efc63cfebd0c7c456830100c0c0bc] | Yes=0.21, No=0.79 |  | True | `38af053d43bee6fd10ce167c7ec063f6c115ad35674bf7eaa12a6da9bd80e770` |
| context | context_unchanged | Will S&P 500 (SPY) hit (LOW) $740 in October? [market=4936037; condition=0xfc754cc715e609a0fac5b4d026924c3bed7d5d3906a1594b37ab88354aa4fffe] | Yes=0.14, No=0.86 |  | True | `a79747258ecf542e1eb2fb2c24d8358993207117c96a5219b1bdbac02f354513` |
| context | context_unchanged | Will S&P 500 (SPY) hit (LOW) $730 in October? [market=4936038; condition=0x22ef1c476f45060abd7a9151f268349a326c8a38216e7585c15992b89b6fdc1f] | Yes=0.085, No=0.915 |  | True | `6b2fa6ac55cb906f2b0741c7ef42723e7011d231cd46f75bf655307f52834393` |
| context | context_unchanged | Will S&P 500 (SPY) hit (LOW) $720 in October? [market=4936039; condition=0xc5b5a2de2cc7cfefe7349e3f48ac0a0499abcf2dfa80afebb1a05c4edaf760ae] | Yes=0.0615, No=0.9385 |  | True | `ca71825ff790d7b2a96b040d9f883e91adb23562be3ab0c7ac4873c0018bdafc` |
| context | context_unchanged | Will S&P 500 (SPY) hit (LOW) $710 in October? [market=4936040; condition=0x8e4af7cd69d6105b0eeb6775690c0cc31eede6f2d52cbefd384653757f18713a] | Yes=0.041, No=0.959 |  | True | `9abcde6f30b2e50d163cf00e6c3d500a204bb64cbf283492471a5df45980b096` |
| context | context_unchanged | Will S&P 500 (SPY) hit (LOW) $700 in October? [market=4936041; condition=0x252215d44373656459b330fcd96448c5b3e4c9675992b736e6ab744d92f2231f] | Yes=0.026, No=0.974 |  | True | `e1e1acd65d3604f13bc66c5ae7f2db174487fc0ff7c75ad58cf9cad87ce43de5` |

### What will Coinbase Global, Inc. (COIN) hit in October 2026?
Group basis: `exact_gamma_event_id`; event ID: `1078044`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 38 | new_to_snapshot | Will Coinbase Global, Inc. (COIN) hit (LOW) $150 in October? [market=5433344; condition=0xc420cd760dd18779c51f90b546bcd33a82f3e3c157d0bcda30b4e2089c6a18b5] | Yes=0.34, No=0.66 | new_to_snapshot | True | `82faee67302eae0cd7c2bf95940671e2323e05f4d1b6290c7e04dcf712490250` |
| 62 | new_to_snapshot | Will Coinbase Global, Inc. (COIN) hit (HIGH) $185 in October? [market=5778263; condition=0x757a35b989f848ec15817b6833453d6ecc38158f6d076b558530c0ba95502cb4] | Yes=0.545, No=0.455 | new_to_snapshot | True | `f6ff572005418e9cab4b9cd7108539d88906347a3b87ccf9d9d518bc80fe87c8` |
| 165 | new_to_snapshot | Will Coinbase Global, Inc. (COIN) hit (HIGH) $180 in October? [market=5778261; condition=0xe0b6ba4bd17fd3620c1a74b02c2bff475463e85a998ca6e524418956d9b99290] | Yes=0.675, No=0.325 | new_to_snapshot | True | `876cc9be77a396b0be77cc1460b742ff091b6bf616afb0a477f870c0fe873db2` |
| 171 | new_to_snapshot | Will Coinbase Global, Inc. (COIN) hit (HIGH) $225 in October? [market=4935945; condition=0x29eff1d60183e5226031886290b704abaf0793913a145e532d3c5acac08f40a4] | Yes=0.1, No=0.9 | new_to_snapshot | True | `61db247ee2579f55935a7343d9bf873d074ade0e8507b76e77fdef4c0966ea8c` |
| context | context_unchanged | Will Coinbase Global, Inc. (COIN) hit (HIGH) $230 in October? [market=4935944; condition=0x11df1799770b99968ea888eef2ac62abc6fc995d535efff20d2995a74cec828b] | Yes=0.0265, No=0.9735 |  | True | `997b3be91788582f584f5b52a2b460f58f384f29d360776d62b69a3ce5cf7f6b` |
| context | context_unchanged | Will Coinbase Global, Inc. (COIN) hit (HIGH) $195 in October? [market=5208033; condition=0x6a90698b3ff6b1b811b5d1ef3dda40b3fe0f161f41dbeaea0ae6f573f20a4aee] | Yes=0.345, No=0.655 |  | True | `fd812c8027b8393a9391e24a044cf174bce4e955b2e365253584294fdd9e50e1` |
| context | context_unchanged | Will Coinbase Global, Inc. (COIN) hit (HIGH) $200 in October? [market=5208035; condition=0xbf087e5e6562c938f210c3fb1505f28f3049a759e69223b127aa479d86023bbe] | Yes=0.25, No=0.75 |  | True | `2d0290c9d7c2fa23bd09fb0b674e0c0a66c2b4d8b198b578a1bcc024b2b194bf` |

## Batch 10 (20 markets)

### What will Amazon.com, Inc. (AMZN) hit Week of October 19 2026?
Group basis: `exact_gamma_event_id`; event ID: `1202011`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 39 | new_to_snapshot | Will Amazon.com, Inc. (AMZN) hit (LOW) $240 Week of October 19 2026? [market=5788682; condition=0xbb0179238301b8421b9c159b149a3b50e81f1cf6466caa43f7b8651a491233fb] | Yes=0.055, No=0.945 | new_to_snapshot | True | `a4b13efd17fc950ba858e4cb8e74ee1137e468fcc43cb99a7da95f992b6791de` |

### French Presidential Election First Round: 3rd Place
Group basis: `exact_gamma_event_id`; event ID: `1178455`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 40 | new_to_snapshot | Will Jean-Luc Mélenchon win the third-most votes in the first round of the 2027 French presidential election? [market=5622516; condition=0x790a5b94de6bf8cce035db2b32c892bf45fdb225fbf964bb8ff2d8d11e720b16] | Yes=0.365, No=0.635 | new_to_snapshot | True | `7d73d40531ab794210b505ca5e494f9eb28b41b15445bece7f16e868ee579c23` |
| 152 | new_to_snapshot | Will David Lisnard win the third-most votes in the first round of the 2027 French presidential election? [market=5622514; condition=0x32773263d589a2bf12fbbea38c309b40dac082e237677245d8dd608638bd7c82] | Yes=0.095, No=0.905 | new_to_snapshot | True | `5367bb99346c28ed453db6bf96ba9bc660c78f748109e14ea8c9e144c5ee797f` |
| 153 | new_to_snapshot | Will Édouard Philippe win the third-most votes in the first round of the 2027 French presidential election? [market=5622511; condition=0x93e2d6f8d78bdbba7e1eff6a10182fd94a724487e4ffc4588418beee609d1d48] | Yes=0.28, No=0.72 | new_to_snapshot | True | `e933b52b6ecff0e47acef80415e06b7c18b82ea29319e79d72c36cf4787c18ae` |

### Pro Football: Cardinals 2026 Win Total
Group basis: `exact_gamma_event_id`; event ID: `912351`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 41 | new_to_snapshot | Will the Arizona Cardinals have more than 6.5 wins during the 2026 NFL season? [market=3887349; condition=0x5161cf1bb880884ee8603b987d09bbe9fcbcabf56ded3971392b64a290546282] | Yes=0.295, No=0.705 | new_to_snapshot | True | `e8c3bde2edc808ea75c1cbc975380e4f69e136d7df456be0a94f7aaad1ade0ab` |
| 154 | new_to_snapshot | Will the Arizona Cardinals have more than 4.5 wins during the 2026 NFL season? [market=3887347; condition=0x9988c0ca695aa4d8526ef014bbc9c48e27bdbeb3099dba4a7d2eed5f52398667] | Yes=0.745, No=0.255 | new_to_snapshot | True | `e4609e0872cc56b0a3d94558e3388ee46fa0929514358f418c9c761358d84dd7` |
| context | context_unchanged | Will the Arizona Cardinals have more than 5.5 wins during the 2026 NFL season? [market=3887348; condition=0xd2cb3adc815890deb173d938e0daeacf95302bb11e7ed5622841d92c0ed51a1a] | Yes=0.535, No=0.465 |  | True | `ff66ae1c3d41c229f3c99af1bb03f6df086c9d2b45fea0818e2b4ff04fcb5416` |

### #3 AI lab by OpenRouter market share week of October 19?
Group basis: `exact_gamma_event_id`; event ID: `1216190`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 43 | new_to_snapshot | Will Xiaomi have the third highest OpenRouter market share the week of October 19? [market=5916289; condition=0xcbc308ec684803d75cdd6cca508f8b68bb342e1693f67870bb8a70c2e7062e04] | Yes=0.016, No=0.984 | new_to_snapshot | True | `5f8fca790c18914ea7931edf40b04d5ae9522e4c3665251c9bfbc1ecd1855df5` |
| context | context_unchanged | Will DeepSeek have the third highest OpenRouter market share the week of October 19? [market=5916267; condition=0x334c86001a4dd52cfe3f04fc97e2d3bdbe350313ddd7a143c9fc361f248bd273] | Yes=0.005, No=0.995 |  | True | `97dd512f916464f18107aab28ef772295118ff45bd5b4aecf9d54eeeb871c380` |
| context | context_unchanged | Will OpenAI have the third highest OpenRouter market share the week of October 19? [market=5916277; condition=0xcb2254b561d1afc5825a21832e7e7f9e195761db41acef31707a82baaf2941ed] | Yes=0.5, No=0.5 |  | True | `060532075cfe8958e4d51b905dcd6f091e7fc93ebf205a9b3b91d3c9c15f2704` |
| context | context_unchanged | Will Anthropic have the third highest OpenRouter market share the week of October 19? [market=5916300; condition=0x9161a3c5ab8d4bfc661673360971be448fcd8fcf91cb10f43a6fd7841ca69f8b] | Yes=0.0205, No=0.9795 |  | True | `4e52a136d8e023cd941b135260068f121d147c727fee455f3f7ccec5f6ca2921` |
| context | context_unchanged | Will MiniMax have the third highest OpenRouter market share the week of October 19? [market=5916304; condition=0xad567e23b50b2ca6507df2be6e5e989c4ab093c75a99a958eede5f4f5fe8f0cc] | Yes=0.002, No=0.998 |  | True | `dc01bbc43287400bb0aba357715e167f815ae220e58e9898c6c9f954e81275bf` |
| context | context_unchanged | Will Meta have the third highest OpenRouter market share the week of October 19? [market=5916309; condition=0x0b441c9bd906b3de387b8385b2fb80ad76124c1030d177a1904e097fa6e822d5] | Yes=0.0015, No=0.9985 |  | True | `71b723e7c325a07b6a1024ebd4eb0729eecaceaf8248afc498ab64c7a5f9f185` |
| context | context_unchanged | Will xAI have the third highest OpenRouter market share the week of October 19? [market=5916316; condition=0xd96aded9b14185c0947293251aa668603edcea1ae122bc79a92119274ccecd7c] | Yes=0.002, No=0.998 |  | True | `3e75188e9a189f3aa09715a17600d4b715697ea6784c78b0920dfc33792debcb` |

### Pro Football: AFC Team to advance to Divisional Round
Group basis: `exact_gamma_event_id`; event ID: `956266`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 44 | new_to_snapshot | Will Houston Texans advance to the Divisional Round in the 2027 NFL Playoffs? [market=4175338; condition=0x0bd58fcf376a572366d2414c9d9cafec37f0406fd4458b6fbcb2080b0da353b1] | Yes=0.1285, No=0.8715 | new_to_snapshot | True | `e2d3eee04408675e7ce9f0129d962937f1df53e5352b0b24c2badc957e0852e5` |
| context | context_unchanged | Will Baltimore Ravens advance to the Divisional Round in the 2027 NFL Playoffs? [market=4175334; condition=0x9a9bbf6424b54952709dd31a057b2bfd8af7dab3c3933102acda00737c1acf05] | Yes=0.525, No=0.475 |  | True | `8f72d66e082e889cf4ecf5a7aec88835e5677757872f38b43294e72b99ec3825` |
| context | context_unchanged | Will Cleveland Browns advance to the Divisional Round in the 2027 NFL Playoffs? [market=4175336; condition=0xf33699efd6c5d30b399bd3c155a632feee166186cf02c055d7961be1bc29879e] | Yes=0.0595, No=0.9405 |  | True | `b8efced324a03aaa7304b2eb870e728e80d59b2dc8819da73287c2e259f5c5ed` |
| context | context_unchanged | Will Jacksonville Jaguars advance to the Divisional Round in the 2027 NFL Playoffs? [market=4175340; condition=0xeb4633c84f5e380faf6b36aa9491bc2b4e9c22bf8f0e2b4ed7b6217bdfcdbd37] | Yes=0.505, No=0.495 |  | True | `5d08a30b502d52f82b4d516a97458733bbcd30cc3ae4140c0ebc4faf02f17486` |

### Oklahoma Senate Election: Turnout
Group basis: `exact_gamma_event_id`; event ID: `870907`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 45 | new_to_snapshot | Will total votes cast in the 2026 midterm election for Senator from Oklahoma be between 1,100,000 and 1,200,000? [market=3697686; condition=0x0417c5c6890fc8abcc01982b77832870e569d999ff08cddc3f33fcc53ff4a971] | Yes=0.38, No=0.62 | new_to_snapshot | True | `caaf395207498c2cfde9b19bcd7508a0211c93e7bc000c7eeb33563905b24f6c` |
| context | context_unchanged | Will total votes cast in the 2026 midterm election for Senator from Oklahoma be between 1,200,000 and 1,300,000? [market=3697687; condition=0x707fc155b1630502008db698083a73387263f663edc5bb77c228b58a0704f013] | Yes=0.345, No=0.655 |  | True | `68282d0b413d1c5c946e4ccc4bfb4cb899eed23a5543fc72723c45480d8899f8` |

## Batch 11 (20 markets)

### Longest GitHub critical incident in October?
Group basis: `exact_gamma_event_id`; event ID: `1108501`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 46 | new_to_snapshot | Will GitHub's longest critical incident in October 2026 be between 3 and 6 hours? [market=5154295; condition=0x229500acfd60e7ff7180e426e950092d7a971c7dd4f112eecc67818450978623] | Yes=0.625, No=0.375 | new_to_snapshot | True | `267b04631c675830b019f7665b5a408210ccea517c73254d497ce018c03b5a5c` |
| context | context_unchanged | Will GitHub's longest critical incident in October 2026 be between 6 and 12 hours? [market=5154301; condition=0x784a11b37f4eb41528d905a4b4368e3a1219e8c5fe390ae9e35690c4c93e10d0] | Yes=0.245, No=0.755 |  | True | `432269c9226bc62626522f984cd3e945e1c981991fb3f519cb1905f0afcd3de4` |

### Oscars 2027: Best Original Song Winner
Group basis: `exact_gamma_event_id`; event ID: `1193377`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 47 | new_to_snapshot | Will "La Nieve" from The Black Ball win Best Original Song at the 99th Academy Awards? [market=5725930; condition=0xc6de9dc0a0864dea708d4cf1893011184c62470c541043e364d7090deb761440] | Yes=0.475, No=0.525 | new_to_snapshot | True | `482a65e635a3a5d3e2d232b7df7545dc3c6ae7a4ac9aa446970e451c6239b710` |
| 78 | new_to_snapshot | Will "This City May Have Chewed Me Up (But It Hasn't Spit Me Out)" from The Debut win Best Original Song at the 99th Academy Awards? [market=5725933; condition=0x67fecc40fed1002f5a6caa7a43d2eaa614d3eb5d8dff296ea3f1d8c08a474551] | Yes=0.155, No=0.845 | new_to_snapshot | True | `900194415da0cf685bb5941967753f0db342d387e304b1d4499df48ee0b60b33` |
| 96 | new_to_snapshot | Will "Let Me Sell You a Dream" from Musk win Best Original Song at the 99th Academy Awards? [market=5725936; condition=0xd8d05a904fdb6b27148cf6ff15b1aae324ced9e8ac281942a9bed4bbebbb3ce7] | Yes=0.045, No=0.955 | new_to_snapshot | True | `54382764319ec5a128c2e1657c2c19f5ebaa152141ef627093953abc542d3ec1` |
| 112 | new_to_snapshot | Will "Runway" from The Devil Wears Prada 2 win Best Original Song at the 99th Academy Awards? [market=5725937; condition=0x409a08d5a4b4162b37cb65c3d93095509d84b3606c2e2e71af6f339b7e6b5fa0] | Yes=0.0165, No=0.9835 | new_to_snapshot | True | `b44daac576c534a7d6a74c186b80098e385f8192163f5a8330dae169bd8dc924` |
| context | context_unchanged | Will "I Knew It, I Knew You" from Toy Story 5 win Best Original Song at the 99th Academy Awards? [market=5725932; condition=0x00f9736b39c8fb806774bc7e6e43a74db284a597221aabc21f5e6bb8ab9680ae] | Yes=0.105, No=0.895 |  | True | `bc2faebd061da22e7d370f7b4f9c1e4d676eccaac9557a0149c2d98c282c91db` |

### GPT Astra 6.1+: Output Token Price Debut?
Group basis: `exact_gamma_event_id`; event ID: `1073352`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 48 | new_to_snapshot | Will GPT Astra 6.1+ debut at an output token price of at least $40 by June 30, 2027? [market=4904282; condition=0xc6dc2d4a2f15d8ec76dd53e9fc042993672a721d0e7a045de832b87790c9baa1] | Yes=0.71, No=0.29 | new_to_snapshot | True | `cc78cd2d67c7803a090d38ff1ee096b887b6e53854aff31e478d7e5cbefa8420` |

### Will Cashmere launch a token by ___?
Group basis: `exact_gamma_event_id`; event ID: `1218408`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 49 | new_to_snapshot | Will Cashmere launch a token by March 31, 2027? [market=5928542; condition=0x9aa52779d5506c727d78f5a64c15a2e303c1f89079efe3f1a82acdc763ecc985] | Yes=0.65, No=0.35 | new_to_snapshot | True | `b7569ca092ddc3f2b7cf448030303f4ec68fcc15bc4000ba3990f62c634fc58c` |
| 95 | new_to_snapshot | Will Cashmere launch a token by June 30, 2027? [market=5928543; condition=0x739996d26d1a01fff21f8c5080b9b97744ab0ff1f99a2bcbdda653c177c0e613] | Yes=0.675, No=0.325 | new_to_snapshot | True | `b56792618caf7d11e5bb2d788968786b2050c45495dd16e7dda5802cbca03850` |

### Pro Football: Eagles 2026 Win Total
Group basis: `exact_gamma_event_id`; event ID: `912449`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 50 | new_to_snapshot | Will the Philadelphia Eagles have more than 8.5 wins during the 2026 NFL season? [market=3887797; condition=0xcb7d38102c3aabcfbbacebfb988b879c7268a4b49554c5d8a7b934c417dd6f2d] | Yes=0.15, No=0.85 | new_to_snapshot | True | `6844317c411539c566146294ee3d9dc4dfc36d78a45c9c98ea2663e588121ea1` |
| context | context_unchanged | Will the Philadelphia Eagles have more than 10.5 wins during the 2026 NFL season? [market=3887799; condition=0x78d1ba8003ddd24bf424b8d8f36176eba97a1618705cae9278376ccde75e6c9b] | Yes=0.08, No=0.92 |  | True | `3dae4f4d456cb738250503cab22629f2e0fe5540e53124bd8982db14499ded0c` |
| context | context_unchanged | Will the Philadelphia Eagles have more than 11.5 wins during the 2026 NFL season? [market=3887800; condition=0xa36a30e13710698421621ef5db08af70019ebdce704ee1e04bfd543c0b17fa27] | Yes=0.065, No=0.935 |  | True | `a9be0b7104482d2679ccb1d613961dc8b1c2bc59afb18deb4f623db7c83ec36f` |
| context | context_unchanged | Will the Philadelphia Eagles have more than 12.5 wins during the 2026 NFL season? [market=3887801; condition=0xa5fdad75d1ff9167ca683eda58112cb9e0617b184df42125ecf589d7a5902a50] | Yes=0.0455, No=0.9545 |  | True | `fa7f035143ae78a7af30e67bf2ce36ef0eecabec55bb7114410d3f498360941c` |

### What will Microsoft Corporation (MSFT) hit Week of October 19 2026?
Group basis: `exact_gamma_event_id`; event ID: `1202004`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 51 | new_to_snapshot | Will Microsoft Corporation (MSFT) hit (LOW) $517.50 Week of October 19 2026? [market=5788637; condition=0x82df63e4f2f231ce238ef91e3d1a7f9122b840bf2deb72f7706d1dc7b8448801] | Yes=0.315, No=0.685 | new_to_snapshot | True | `9471b10d24b0bd26de4b9df3773b59e8f7156bf8e647008f8d1052a8052e334a` |
| 109 | new_to_snapshot | Will Microsoft Corporation (MSFT) hit (LOW) $510 Week of October 19 2026? [market=5788639; condition=0x716a1ff6519c24f2d395e1ad5645c13ba20e9e02e0938bbb3a49cd3455ad5269] | Yes=0.135, No=0.865 | new_to_snapshot | True | `b431488c01ce37a0bb4fc94fb0f5bf2b6d54d7de3d5363bcfd2a68e7afe5164f` |
| 236 | changed | Will Microsoft Corporation (MSFT) hit (LOW) $480 Week of October 19 2026? [market=5788644; condition=0x2f0c6c2524503e9774c077d53ff5de1debda77f31c4c5c7e00216181d4676adb] | Yes=0.029, No=0.971 | best_ask, spread | True | `d0a96519d1f787b07575a19874872cc2c20b473b5f8ec9e6ee86afa6b80fb6f4` |
| context | context_unchanged | Will Microsoft Corporation (MSFT) hit (HIGH) $540 Week of October 19 2026? [market=5788629; condition=0xbc7c60de762ba1aec148a1ec5d2c7b0daf57c1258d2884688d25c3b5756aa122] | Yes=0.65, No=0.35 |  | True | `5c89832a0bd466ba5ea90e8774a8ad14e28f1b04c55ade32c6443ba6e68a1371` |

### Will any contestant beat Luke Littler?
Group basis: `exact_gamma_event_id`; event ID: `1200388`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 53 | new_to_snapshot | Will any contestant beat Luke Littler? [market=5777915; condition=0x1031b494f0560db2cf0894b8f11d4f11537d688d7f3de18f87766a4ddf110d59] | Yes=0.46, No=0.54 | new_to_snapshot | True | `ae737629b87820e20999baca5b711f5047eeb6da7b43ac37e08a098259d08bc0` |

### MLB: AL Rookie of the Year
Group basis: `exact_gamma_event_id`; event ID: `307813`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 54 | new_to_snapshot | Will Kevin McGonigle win the 2026 AL Rookie of the Year award? [market=1719961; condition=0x29663a900121eee8d9a969a3edb7f8649d5e58f16af2684f01dd877f5ab5fc2d] | Yes=0.9375, No=0.0625 | new_to_snapshot | True | `7aff2b690c61b8ce71caa8996d66872df0fd41186f82eee1620af676c060b852` |

## Batch 12 (20 markets)

### Second-best AI Lab end of December?
Group basis: `exact_gamma_event_id`; event ID: `1113965`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 55 | new_to_snapshot | Will Anthropic be the second-best AI lab at the end of December 2026? [market=5176985; condition=0xb5f204b9d8b79fa9615022212c91a239cdb45f13d9b93028bc1611f7f2f79e97] | Yes=0.32, No=0.68 | new_to_snapshot | True | `914ccb26077abebce0beaec9851fe9085950ffe11c4b013a8a1976f45769f975` |

### Highest OpenAI score on Humanity’s Last Exam in 2026?
Group basis: `exact_gamma_event_id`; event ID: `740958`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 56 | new_to_snapshot | Will the highest score achieved by an OpenAI model on Humanity’s Last Exam in 2026 be 55% or higher? [market=3072352; condition=0xd30e3b4e2d6bf4594f44ad982b55435c3add71d3622993b0dee67354defaf598] | Yes=0.76, No=0.24 | new_to_snapshot | True | `e986ef77457356a5665489f3497641a6c932e89069cc1cf3a35f74f7074c6bb7` |

### What will Coinbase Global, Inc. (COIN) hit Week of October 19 2026?
Group basis: `exact_gamma_event_id`; event ID: `1202041`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 57 | new_to_snapshot | Will Coinbase Global, Inc. (COIN) hit (LOW) $162.50 Week of October 19 2026? [market=5789038; condition=0xefc59ed2d57a490491db0672c5986e9870e0c5a4ddc6e989768814b319895515] | Yes=0.535, No=0.465 | new_to_snapshot | True | `a6fb99e09ae57957e98abb29fdfcadd503a6686c83b87bcdcad33db99adc5bd9` |
| 81 | new_to_snapshot | Will Coinbase Global, Inc. (COIN) hit (HIGH) $185 Week of October 19 2026? [market=5789029; condition=0xc53fe91b38afe881398d77391576aa14423451fedda350eb7dd53b645ff0df12] | Yes=0.29, No=0.71 | new_to_snapshot | True | `5ac41ca75b4b61869b1698f557934a387e4b7375f584e7ca1198ef5c468d72e9` |
| 201 | changed | Will Coinbase Global, Inc. (COIN) hit (LOW) $167.50 Week of October 19 2026? [market=5789036; condition=0x404febea69ed4515399b93886913999d19573dcd399b7b67afa629bc496f4231] | Yes=0.785, No=0.215 | best_ask, best_bid, no_price, yes_price, outcome_prices | True | `2e697afa30ff36e999d5c5de7ff673a3e6626d5240e07def0ea6a7bf051e9476` |
| 233 | changed | Will Coinbase Global, Inc. (COIN) hit (HIGH) $180 Week of October 19 2026? [market=5789031; condition=0x5322f1faa2fc4a4629a2beb95083b0ca0cc8a5fb5d633da018643d6c3ab0cf00] | Yes=0.465, No=0.535 | best_ask, best_bid, no_price, yes_price, outcome_prices | True | `436aaa00d914f97787870775a9a0f9e4b523e37466d68eb2c017b7470b828f98` |
| context | context_unchanged | Will Coinbase Global, Inc. (COIN) hit (HIGH) $190 Week of October 19 2026? [market=5789027; condition=0x42121478ac2c9e538a813467394693f98ae480f990aadfe832a00ed73ed9c45e] | Yes=0.175, No=0.825 |  | True | `48b237306624b808ab48ba58ca2cc036300fb3f19e7595d1c20b5ab83aa92df8` |
| context | context_unchanged | Will Coinbase Global, Inc. (COIN) hit (HIGH) $187.50 Week of October 19 2026? [market=5789028; condition=0x03c7f89d0e558dcc383a75cc2dd39fcd444a420d0233249409bf9ca8a24c3e1a] | Yes=0.235, No=0.765 |  | True | `48710c5627da091505bf7018eda32f912996fe3c7392dda68d535d125a88bce4` |

### Bundesliga: Most Clean Sheets 2026-27
Group basis: `exact_gamma_event_id`; event ID: `872122`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 58 | new_to_snapshot | Will Manuel Neuer (Bayern Munich) record the most clean sheets in the 2026-27 Bundesliga season? [market=3706806; condition=0xec99a242eebefd4db7f9e32c4dc87e6b4e2e19aee533ce3a5511c4ea84fa5c71] | Yes=0.11, No=0.89 | new_to_snapshot | True | `565b7d26ad3ac557270eb996cfbeb23359e4f81cf4b4bf646c4760be00df1d6c` |
| 99 | new_to_snapshot | Will Gregor Kobel (Dortmund) record the most clean sheets in the 2026-27 Bundesliga season? [market=3706807; condition=0xa8f432c2245de9cfd02ae60e86ed1b857ddb99d53331f27b0b2d4da33be05293] | Yes=0.474, No=0.526 | new_to_snapshot | True | `0652364318a2f8a8430ca15927d5977103f3bbbf11e8e43e543aa8f4785bb70d` |

### #1 Spotify song in the US this week? (October 23)
Group basis: `exact_gamma_event_id`; event ID: `1207549`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 60 | new_to_snapshot | Will "Lies - Zach Bryan, Lana Del Rey" be the #1 US song this week? [market=5837545; condition=0x9f838a0209616ddfa5d10013a014bf6d7be95afa49de4db10d9af9c4c75a5a08] | Yes=0.0155, No=0.9845 | new_to_snapshot | True | `28c065365485e18f4ad8fbace926d3a130658ecaeb5a7501c71783dc23391bb5` |
| context | context_unchanged | Will "Patient Zero - Taylor Swift" be the #1 US song this week? [market=5837539; condition=0x7688f58b8a903a88c1150bc5bca8167f00a9441aa93e03a94eed76b2184863fd] | Yes=0.0025, No=0.9975 |  | True | `4930db2a521f448078b1679fdf67a088cffecdad9a714f32f376f2429843787e` |
| context | context_unchanged | Will "Choosin' Texas - Ella Langley" be the #1 US song this week? [market=5837541; condition=0x57b35595fbf87121f00cb70498b1e604f8408201a2a986b3ab4a7fe114067f06] | Yes=0.002, No=0.998 |  | True | `0c5f8ea6b741c33e36fe247b2140957c1584c2661bf5d64dc250854b1a5223d4` |
| context | context_unchanged | Will "Earrings - Malcolm Todd" be the #1 US song this week? [market=5837542; condition=0x5241caf81d27ed7a5f0fe4a6f08eda2531e2d10b3108e833d0e446923455f8cd] | Yes=0.0015, No=0.9985 |  | True | `f3cf09ef0d6b1c0209627b43bd2e53d4050711431f61ddeaebf59531965bda13` |
| context | context_unchanged | Will "BbY WOW - KAROL G, Judeline, rusowsky" be the #1 US song this week? [market=5837543; condition=0x2ca41656851b6a65321f9c269f50ccd8cef7685c67e9accbabc08f19e7116aca] | Yes=0.0015, No=0.9985 |  | True | `6657110612681dd306f078d71b1906bbe3422bf1fe7737698fe2b6d81af6fab1` |
| context | context_unchanged | Will "expectations - Olivia Rodrigo, Chappell Roan" be the #1 US song this week? [market=5837544; condition=0x36c3db90cffc68bb4cd062160e100b675e71f69fc2dfac5b62a331a0956e1a99] | Yes=0.0025, No=0.9975 |  | True | `100be50d4bc68df773398537b48a287d5862572f7ea79aa2fbd698da2c5ba54f` |
| context | context_unchanged | Will "Housewife - Tate McRae" be the #1 US song this week? [market=5837546; condition=0x900d8f556c2da54de8afcd24225c320c28c8156086ef0398be57a8cb14bcf0cc] | Yes=0.927, No=0.073 |  | True | `d80fad47ed5c57acb989fe1d33e65540c8f10d825d7449fa84b1ccf5ecf8e3a0` |

### Will Russia invade a NATO country by...?
Group basis: `exact_gamma_event_id`; event ID: `25413`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 61 | new_to_snapshot | Will Russia invade a NATO country by December 31, 2026? [market=2749367; condition=0x4b7b21a5cfdcc7cbb33d499c44b7f11ac754f13d3db39cd93b976141dcdb516e] | Yes=0.045, No=0.955 | new_to_snapshot | True | `0692d2be856c346b6cfa38a66d56e063c1f5d95b40ae1cfd25f242ff35d3b47b` |

### NCAA Football: Illinois 2026 Win Total
Group basis: `exact_gamma_event_id`; event ID: `838845`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 63 | new_to_snapshot | Will Illinois have more than 5.5 wins during the 2026 CFB season? [market=3540049; condition=0x7687fe5d555b0e7063073560fbbecbb64ad874f97e18278345648c3b71df3e0e] | Yes=0.335, No=0.665 | new_to_snapshot | True | `fbf73a3415a48aa9c24f62c309e41dd3196fecabe0aecbd4caff8f095479770f` |

### Will Wildberries announce a bankruptcy before 2027?
Group basis: `exact_gamma_event_id`; event ID: `744027`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 64 | new_to_snapshot | Will Wildberries announce bankruptcy before 2027? [market=3085137; condition=0xbef8c052aca381908541276ef2e56f3b1920599750b1d7e10dbd306f65b08c70] | Yes=0.061, No=0.939 | new_to_snapshot | True | `f36b634092ae3cbd026a6c57efd07893dc7ca5754fd92f8b1b31a4f16b13df2d` |

## Batch 13 (20 markets)

### Serbia Election: Student List Vote Share?
Group basis: `exact_gamma_event_id`; event ID: `1082278`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 65 | new_to_snapshot | Will the Student List win 35-40% of the vote in the 2026 Serbian parliamentary election? [market=4962436; condition=0x0c88efe616f49edd58f65c2b934dcd7d861408da3625c77db85c966b1ac3131e] | Yes=0.28, No=0.72 | new_to_snapshot | True | `0cc4d12fd0afb7d8c7b58018800b0d12ed1e23c7615b6832373b3f52a4ae2153` |

### What will Rocket Lab USA, Inc. (RKLB) hit in October 2026?
Group basis: `exact_gamma_event_id`; event ID: `1078042`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 66 | new_to_snapshot | Will Rocket Lab USA, Inc. (RKLB) hit (HIGH) $60 in October? [market=5742895; condition=0x03b0e3ab9f847e1f8aaf3f1f92bbde75b4a07f71c624a9d7165052c734dab2ef] | Yes=0.26, No=0.74 | new_to_snapshot | True | `4b336a190328bfee312d4f71a4ef8cabb397bbb50609c0c12b86659ac3592c30` |
| 69 | new_to_snapshot | Will Rocket Lab USA, Inc. (RKLB) hit (LOW) $48 in October? [market=4935922; condition=0xce69ffdee5153012041b315bf2cb85a51fe516ff3df29259f389bb9c63e6ef24] | Yes=0.507, No=0.493 | new_to_snapshot | True | `9fc79140cf16ead9f758a527e233a12a3969495158735e5988b3e67b83127d2d` |
| 110 | new_to_snapshot | Will Rocket Lab USA, Inc. (RKLB) hit (HIGH) $56 in October? [market=5742893; condition=0x6437137d76331bb929915eeccaf56d7f93bff76180f235a29500af6cd016d538] | Yes=0.568, No=0.432 | new_to_snapshot | True | `429a9be73a196aae65ca4fd6ef24e62237ce213a8c2f95e6b72d1f305ff76e99` |

### NC-02 House Election Margin of Victory
Group basis: `exact_gamma_event_id`; event ID: `834099`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 68 | new_to_snapshot | Will the Democratic Party candidate win the 2026 NC-02 House election by 40%-45%? [market=3518545; condition=0x5a0f7b0f1291e28829ac29857340d754e135c7d36473004126740e5a7fc77b9a] | Yes=0.327, No=0.673 | new_to_snapshot | True | `cecadc548c0c0a127784bbd032433b69541c8e9171ebecddf62160bc0f916291` |
| context | context_unchanged | Will the Democratic Party candidate win the 2026 NC-02 House election by 30%-35%? [market=3518547; condition=0x3547bcfcc85bb13ea4550f9a1234d2db04186a3e8acfc693f45b8642f8dcdbe9] | Yes=0.0445, No=0.9555 |  | True | `2b354e3e1184352018d5de2cbbb86320a09fa152d96c2efc63c2b1b4b63e7ef5` |

### #3 AI Lab end of December? (Style Control On)
Group basis: `exact_gamma_event_id`; event ID: `1113966`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 70 | new_to_snapshot | Will Anthropic be the #3 AI Lab at the end of December 2026 (Style Control On)? [market=5177254; condition=0x6935ba2e0b63f33af908da29f74e78a58151b15515e977e38500665a117e087d] | Yes=0.23, No=0.77 | new_to_snapshot | True | `2c93a6ed2e7a3c1d9b357a3bc7c718532549a8da677cc0568f4a718ec71bee1e` |
| context | context_unchanged | Will Meta be the #3 AI Lab at the end of December 2026 (Style Control On)? [market=5177255; condition=0x57d69d96d34c0493c85aff77da2501cb251e29f30940b5d134ef0e0d00608f49] | Yes=0.38, No=0.62 |  | True | `4f78435a7fedd902ce41e62b278b76a636cca2d944f55d94cbd03abcab8338ed` |

### Reserve Bank of Australia Decision in November
Group basis: `exact_gamma_event_id`; event ID: `829777`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 71 | new_to_snapshot | No change in Reserve Bank of Australia's interest rates at the November 2026 meeting? [market=3499789; condition=0xc5bd8359c8be2ed801f29eca7f2c372eca50bd9d075f4d36a06ca65b21b5942c] | Yes=0.755, No=0.245 | new_to_snapshot | True | `f2d593f3148c4c6c26aebdf39c7210981a4ce1c06172ea0454a3f9198a31c51b` |
| context | context_unchanged | Reserve Bank of Australia decreases interest rates by 25 bps at the November 2026 meeting? [market=3499788; condition=0x51ce8f0b70cefd77fd684590a9569bcc0ce8466191a10ea031bf561e239e068e] | Yes=0.0015, No=0.9985 |  | True | `5a111a3e2d7acaa2aeda428c8706309c6fde8ccd422382fa66cb04a48f1859e1` |
| context | context_unchanged | Reserve Bank of Australia increases interest rates by 25 bps at the November 2026 meeting? [market=3499790; condition=0xc55e2bb43b89ecbdb1a9bcb0cde684e3f2108faf1d7502ca6032b260c9aed81f] | Yes=0.235, No=0.765 |  | True | `1c99f5619d92d8e98233ea2951012110fc795f3d0415950d37b5f5a628a39364` |
| context | context_unchanged | Reserve Bank of Australia increases interest rates by 50+ bps at the November 2026 meeting? [market=3499791; condition=0xe2edd12d540508783266d9d8b0b9bca151b9f1deb3188a35262660f87f65aa22] | Yes=0.0015, No=0.9985 |  | True | `9fd7181fb8483682b247561525f498a48ed61e00a1db6499b285149eb78ab8d7` |

### Yum! Brands (YUM) Q3 worldwide same-restaurant sales growth?
Group basis: `exact_gamma_event_id`; event ID: `1194103`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 72 | new_to_snapshot | Yum! Brands (YUM) Q3 worldwide same-restaurant sales growth -0.5% to 0.5%? [market=5730112; condition=0x313be38c5f330aa795a98f05e0dc6362db2a1a26643d712fbc25dfacb3f94a94] | Yes=0.39, No=0.61 | new_to_snapshot | True | `a4d35f4888427f242c98f4d83359a4017b893f5e333f19e7444133ebd617b89a` |

### Oscars 2027: Best Adapted Screenplay Nominations
Group basis: `exact_gamma_event_id`; event ID: `1188313`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 73 | new_to_snapshot | Will "Ink" be nominated for Best Adapted Screenplay at the 99th Academy Awards? [market=5686302; condition=0x7ac807451666bc3fd97e51f99329ef84eaf448abb5ae11d0ddfe3b0c5dcaaaa3] | Yes=0.26, No=0.74 | new_to_snapshot | True | `6923d17a88014fca3492b94c442ceecb73b0daf768d753712a51afc644678695` |
| context | context_unchanged | Will "The Further Mis-Adventures of Cliff Booth" be nominated for Best Adapted Screenplay at the 99th Academy Awards? [market=5686298; condition=0x90975e117b48e0bcc0b5f99795980764002abf74d65c1df79ba87aa79565cf13] | Yes=0.0305, No=0.9695 |  | True | `fa465f9d987c1b9090f5e65b92279f404275e0f282ace6c544ef69ad88b047ae` |
| context | context_unchanged | Will "Wildwood" be nominated for Best Adapted Screenplay at the 99th Academy Awards? [market=5686304; condition=0xcaa0aadfd0b372f0980770e8dd823b6aaa9fea4479f4903b2302eaf8d6f0036a] | Yes=0.04, No=0.96 |  | True | `46dc4f8b7de2c27082ee30cc20470a6ae85a246fb58aaad989d890b8b79228de` |
| context | context_unchanged | Will "Toy Story 5" be nominated for Best Adapted Screenplay at the 99th Academy Awards? [market=5686310; condition=0xaf8657cb5f90ec840378bafd15d7781d7369e99c44ac21745a7fb5fa5ee8f462] | Yes=0.031, No=0.969 |  | True | `f25364b2ecb928609c8d8964c2ae5c9729458885a77dc67113fb7e394e0eaefd` |

### Montana Senate Election Winner
Group basis: `exact_gamma_event_id`; event ID: `57660`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 74 | new_to_snapshot | Will an Independent win the Montana Senate race in 2026? [market=630833; condition=0x3b5260e993f1eb6e127dffa8ee40b29a30a7b7343ad1041c33c389e15810c565] | Yes=0.0825, No=0.9175 | new_to_snapshot | True | `c6d1610f12278b62756f7a2bbe80f08dc51d1750d5fb9b5877d3eb1fa660de25` |
| 111 | new_to_snapshot | Will the Republicans win the Montana Senate race in 2026? [market=630832; condition=0xd103195d48bf6183e28c4140bd374dd3e907e8f8d411374cb4d2d124ec4c216d] | Yes=0.915, No=0.085 | new_to_snapshot | True | `c250eb11b74f1a5489a2967cd2ddd3cd19b16e60abd6dc90520a9b976e0a6b43` |
| 194 | new_to_snapshot | Will the Democrats win the Montana Senate race in 2026? [market=630831; condition=0x1bbb01c67b1520c5db8e02c65b395176b7e2b43d16cc8f8810beb64d70f6e69b] | Yes=0.0015, No=0.9985 | new_to_snapshot | True | `ec7cee8b00c626525ed452cbab83d7614550a51437f1c100d6b9d811c3abe03e` |

## Batch 14 (19 markets)

### Netflix (NFLX) closes week of Oct 19 at ___?
Group basis: `exact_gamma_event_id`; event ID: `1202027`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 76 | new_to_snapshot | Will Netflix (NFLX) close at $110-$120 on the final day of trading of the week of Oct 19 – Oct 23? [market=5788859; condition=0x2828559d7e94a27f37469c4e35ef924630988528e2f30d7bd321d827aec8e1a6] | Yes=0.0045, No=0.9955 | new_to_snapshot | True | `5864235a44a822a4f7c72ff05bcda71a84da9f941e4598405801394adfcb6140` |
| context | context_unchanged | Will Netflix (NFLX) close at <$30 on the final day of trading of the week of Oct 19 – Oct 23? [market=5788840; condition=0x5058339e38416f131c9bc1056d880b7d39efff95d2607fd6260df2eb570ff6d8] | Yes=0.0045, No=0.9955 |  | True | `b343bc8c2b9fa1ad6422ea218ef1905dedf5dd6400eac87e6b119dfb4cabe9c1` |
| context | context_unchanged | Will Netflix (NFLX) close at >$120 on the final day of trading of the week of Oct 19 – Oct 23? [market=5788861; condition=0x30692b803687eba1808c3e5c2343a4142401e5a9c78ba416fc8372cd5361f50c] | Yes=0.0045, No=0.9955 |  | True | `250a95b83efd4c075d2396a805eda1f1b39de67ea76f29d1ee770cbef1bc725d` |

### Will Russia capture Bilytske by...?
Group basis: `exact_gamma_event_id`; event ID: `164330`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 77 | new_to_snapshot | Will Russia capture Bilytske by October 31, 2026? [market=5164680; condition=0x8c817ce9c94f666961cb5568cced10afc4ab0c31288a63e178021756d745061a] | Yes=0.21, No=0.79 | new_to_snapshot | True | `b73d9ba67646b3fd5e3761744056b127c7187b099930b16779d3e9049aa4e7b5` |
| 91 | new_to_snapshot | Will Russia capture Bilytske by December 31, 2026? [market=2373826; condition=0x07c7dc52d4acfee3570262251b638234684781e6438da839920e9d2a4af5f8c4] | Yes=0.855, No=0.145 | new_to_snapshot | True | `e8943c8090a16dcbe8a021213dc37cb17609cd55f6138a49ed91949ebb3fb593` |

### Third-best Code Arena WebDev AI Lab end of October?
Group basis: `exact_gamma_event_id`; event ID: `841229`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 79 | new_to_snapshot | Will OpenAI be the third-best Code Arena \| WebDev AI lab at the end of October 2026? [market=3554625; condition=0x9eb3299c7db58f27079d396d69b9059aaf73d02d5b964bf956c2adcb0ec5b05f] | Yes=0.02, No=0.98 | new_to_snapshot | True | `2b16bd81773c441f6148a20850f3917477779bdefc2aa20e9574d6de425973e5` |
| context | context_unchanged | Will Anthropic be the third-best Code Arena \| WebDev AI lab at the end of October 2026? [market=3554624; condition=0x0a130aa7f770b5eef70c0361c00aae9b78958e22b20add2a63805d8ffb0d0a69] | Yes=0.0245, No=0.9755 |  | True | `7deb452b135f44fc0bbc4a7b997a8b8846b75ecfe6f6be19c41cb7fbcf66eab6` |
| context | context_unchanged | Will SpaceXAI be the third-best Code Arena \| WebDev AI lab at the end of October 2026? [market=3554627; condition=0xdf13776a5b0b6d3c5299185f7645478e338a6a9b036051d5921438e680388957] | Yes=0.0095, No=0.9905 |  | True | `d485789c9b1e066da729da13d05966b34604d690f6c7ece789cdda331cf9dedf` |
| context | context_unchanged | Will ByteDance be the third-best Code Arena \| WebDev AI lab at the end of October 2026? [market=3554629; condition=0x8239a9946df56767e996cd9523388e8b3a8b6c10b5bde42b69a9483fe0df5604] | Yes=0.0035, No=0.9965 |  | True | `91cbb81d8b1594d8e07050e806de21759306e779ba5f47089afed8cc6cbb0564` |
| context | context_unchanged | Will DeepSeek be the third-best Code Arena \| WebDev AI lab at the end of October 2026? [market=3554634; condition=0xb5746f176efc7837ebd4f10f6475557abfaf4597370ededb94c1fb08672f2e0f] | Yes=0.0065, No=0.9935 |  | True | `574fac37122ae1f847620caec12b78b9e026dfcd68d2b3c067f7603ab777a9a8` |
| context | context_unchanged | Will Thinky be the third-best Code Arena \| WebDev AI lab at the end of October 2026? [market=3554635; condition=0xe2f19ae31b424018f762e275ac3530e28058751f0c153eefd697c586a7b8ddc9] | Yes=0.005, No=0.995 |  | True | `a9f0d6c7f207aa00ac27796c20a7451a27dff33579598eaf9fa0b7c6621c1a28` |
| context | context_unchanged | Will Tencent be the third-best Code Arena \| WebDev AI lab at the end of October 2026? [market=3554636; condition=0xc7e8e0c6a01f985f2f920147bae7dc6395172edb531d7618b5363455f5dd88e6] | Yes=0.0025, No=0.9975 |  | True | `68a4266bc3f388834ea4be91b2d1a2ce79bdd3c4e957a1bf2eaea1cf164d2b51` |

### Pro Football: 2026-27 1,000+ Receiving Yards
Group basis: `exact_gamma_event_id`; event ID: `927517`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 80 | new_to_snapshot | Will Ja'Marr Chase have 1,000+ receiving yards in the 2026-27 NFL regular season? [market=3959706; condition=0x584f0f47faaaf414ca87bd2a274db51897a8c77ab469c583685eef18a61dbebd] | Yes=0.69, No=0.31 | new_to_snapshot | True | `53abe5b6f59d2162210683808ab865beaa74a40722fd0a2c35206a35440b9968` |
| context | context_unchanged | Will CeeDee Lamb have 1,000+ receiving yards in the 2026-27 NFL regular season? [market=3959710; condition=0x5447699d333116713de6faa0dabcf443c00cb9176d7503ef34083b34c3ff9dac] | Yes=0.87, No=0.13 |  | True | `ab234948cdbabc83f2d5c3d33121e9e2f2c5a6cd79e83964e0a039506daa5d4f` |
| context | context_unchanged | Will George Pickens have 1,000+ receiving yards in the 2026-27 NFL regular season? [market=3959720; condition=0x01b5ccb31f64af24f1acff871f12835936e436bd9c559f36650635e6ecc23724] | Yes=0.69, No=0.31 |  | True | `e49ccafa157dff0451bf36290858ec2bee23249334b06303265140afdf539ae5` |
| context | context_unchanged | Will Emeka Egbuka have 1,000+ receiving yards in the 2026-27 NFL regular season? [market=3959725; condition=0x6b2cc211631e6d01e693138c5c5c000d561791599251c02aa73cc470e4fe1f34] | Yes=0.185, No=0.815 |  | True | `ab2f8ed65daaa0b7f34a66edef4d23942b77f42a17aad3e5b1cfceda44928196` |
| context | context_unchanged | Will Christian Watson have 1,000+ receiving yards in the 2026-27 NFL regular season? [market=3959744; condition=0x813873c53694108e4a4d3f206ecc4fb33c5de7906a4c51e0a84ce0732bc274e1] | Yes=0.875, No=0.125 |  | True | `c1fb2232061c5cafb199a9a73d99d3ec83a40cf2c5bdd37eb9ae462bc258ad36` |
| context | context_unchanged | Will Josh Downs have 1,000+ receiving yards in the 2026-27 NFL regular season? [market=3959752; condition=0x0b7539cf1812b5f7874170b6fe089b23847c9403e9cc17b9b8beabf0611d1739] | Yes=0.14, No=0.86 |  | True | `8b951510929f93fa2e9163bbad30272ad600473c713070c2956c55f435ec2c43` |
| context | context_unchanged | Will Malik Nabers have 1,000+ receiving yards in the 2026-27 NFL regular season? [market=3959769; condition=0x38a16e5b4966d1f66f2f87cc43afbaeaedd70c492d2b1729c05c0d8d6b990ba8] | Yes=0.695, No=0.305 |  | True | `1a72dac2ab128086d8d710d2819bde53906685758f709de67b0dae2d98dc0b8f` |

## Batch 15 (18 markets)

### UEFA Europa League: Team to advance to 2027 Round of 16
Group basis: `exact_gamma_event_id`; event ID: `956316`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 82 | new_to_snapshot | Will Torreense reach the 2027 UEFA Europa League Round of 16? [market=4175672; condition=0xf09f1cb9fcb5664d9ba31589c1795e3f2b48e8cd5b80185af942a4acf1118047] | Yes=0.185, No=0.815 | new_to_snapshot | True | `a8c772e0ff312cf37dd437b4315e648d12ddc59b53ccb5f14ecbc1b8e84d91e0` |
| context | context_unchanged | Will Real Sociedad reach the 2027 UEFA Europa League Round of 16? [market=4175657; condition=0x1df3288f18f231018a308a610812a886e7c4d43b79452c78d0292df175589038] | Yes=0.515, No=0.485 |  | True | `fa79f13b63a22a95e7ae4bfd8bb57be74a9f06b4b48f3dac0856baa002d667c9` |
| context | context_unchanged | Will TSG Hoffenheim reach the 2027 UEFA Europa League Round of 16? [market=4175662; condition=0x9d2eae621fbce3879b7a096351362a3c57089b2b4276b78a25c12ffccefef56d] | Yes=0.435, No=0.565 |  | True | `80f316d46ad8b459a599f74ad1854b45eef27883044709b2550d6f676ae8bab7` |
| context | context_unchanged | Will Bayer Leverkusen reach the 2027 UEFA Europa League Round of 16? [market=4175664; condition=0xdbfffc68b14997050ed4f19873f608c490edc24e97fdca9b33d6fd52f8aed640] | Yes=0.9575, No=0.0425 |  | True | `ed24e3023b2ff0c0ea7e2fb316edb056502295a7e50ac681f626076f6892199b` |
| context | context_unchanged | Will Marseille reach the 2027 UEFA Europa League Round of 16? [market=4175666; condition=0x1a93740c50cdb10c7fa2532344a2fdf12360a63c344b30241f4c14f8186416f5] | Yes=0.345, No=0.655 |  | True | `cbb5c41dbc468c557586f12fa508e004596628ad944caebb7cdc490811cced31` |

### Amazon’s Market Cap end of 2026?
Group basis: `exact_gamma_event_id`; event ID: `800876`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 83 | new_to_snapshot | Will Amazon’s market capitalization be between $3.00T and $3.50T at the end of 2026? [market=3358961; condition=0xd15c8bbe94a4bb619edf8416777264999572311c04d7339a160a2a6ffc297856] | Yes=0.21, No=0.79 | new_to_snapshot | True | `f646c576653f6186f4b3b48044febd0f37b6394c91612105b08f7baf81de5313` |

### Serbia Parliamentary Election: Turnout
Group basis: `exact_gamma_event_id`; event ID: `1082040`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 84 | new_to_snapshot | Will voter turnout in the 2026 Serbian parliamentary election be 70% or more? [market=4960837; condition=0x287fac2828d12b9ab36a145b5514ecbb10287a76fe0063ccc6e8eccde32a9970] | Yes=0.175, No=0.825 | new_to_snapshot | True | `d221110bfdd4e477a80d47341d928ebb425937f085607e3ed3c484d371c68cda` |
| context | context_unchanged | Will voter turnout in the 2026 Serbian parliamentary election be less than 58%? [market=4960828; condition=0x9fb60878c477230a612315f0eed23c4d60c91a0a773cdc2e814c718fa9f08fec] | Yes=0.0445, No=0.9555 |  | True | `e9b2b237ef7bffc45a9d95ad69fc1e0bee82d3ff52710d9981c3c0ba8b38e78e` |
| context | context_unchanged | Will voter turnout in the 2026 Serbian parliamentary election be 62-66%? [market=4960833; condition=0xfbcc2861e7cdb24eeaca84847552566d4b43ff921c93c544ef88304be8c984b5] | Yes=0.375, No=0.625 |  | True | `3b2fa087263a562ed7d85f05cc02ef51432c6a40b581319e342c73e189c8209f` |

### Which companies will the US take a stake in?
Group basis: `exact_gamma_event_id`; event ID: `197077`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 85 | new_to_snapshot | Will the US federal government take a stake in Pfizer Inc.? [market=1323331; condition=0x1e4ae24fb0a3f204679a8d860d34b0935381d35a6c7bc0713ee9e56451cf1d3c] | Yes=0.0525, No=0.9475 | new_to_snapshot | True | `6b932536cf5e59c3b8e65bf48cf1be58cc15376c4300c4a9ac064423c31a5791` |
| 137 | new_to_snapshot | Will the US federal government take a stake in Anduril Industries, Inc.? [market=1323315; condition=0x11c846106277b0b0eccd71a5c7297073c646bf5a19a8ef92b2f9305e97e2be38] | Yes=0.24, No=0.76 | new_to_snapshot | True | `798f0ea9ff0c6422e2206e3ab351773782e5d467133399134f224513b9b807e8` |
| 177 | new_to_snapshot | Will the US federal government take a stake in Micron Technology, Inc.? [market=1323326; condition=0xec8dc021aeb7c770c0f551da37b9f1aee4e7b97834ab12f51b524ed269c8487a] | Yes=0.07, No=0.93 | new_to_snapshot | True | `8f923165558813f450149f0bc4a83980ce41f2addc92b776555b63b817121ec8` |

### What will NVIDIA (NVDA) hit in October 2026?
Group basis: `exact_gamma_event_id`; event ID: `1078038`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 86 | new_to_snapshot | Will NVIDIA (NVDA) hit (LOW) $168 in October? [market=5824831; condition=0x448a758784e6c0340fbf4e0b47d4df47bedfc10f49989ff52ebbdbc3667e2541] | Yes=0.01, No=0.99 | new_to_snapshot | True | `4ebcac3a298c0b617a008bfb01ec5d6b203c60d5bba9d78af0f9d7d3866234c6` |
| 119 | new_to_snapshot | Will NVIDIA (NVDA) hit (HIGH) $248 in October? [market=4935835; condition=0xc6b425d2c4e6d8db8295732c778adbcba482d4c0aa2060e70da8cdbc190a2089] | Yes=0.0555, No=0.9445 | new_to_snapshot | True | `4f622f6bccc3c25a11a444d417009be156e888e06be41db0932f05457f81b353` |
| context | context_unchanged | Will NVIDIA (NVDA) hit (LOW) $200 in October? [market=4935841; condition=0x04c941113a8388c0417e7c2bf66b826731f7c1f1c5a9ab4b36618fc876cfe7ce] | Yes=0.1585, No=0.8415 |  | True | `c070e9d660b1042270e5345db816218c04d186c3319ab5773c5e21dc7759af89` |
| context | context_unchanged | Will NVIDIA (NVDA) hit (LOW) $184 in October? [market=4935843; condition=0xee7a76bcb97c2976b5f2bdd5b0bc58bd738443720ebbb6a6dd4896f173cc9c56] | Yes=0.028, No=0.972 |  | True | `b0ddf7a1d34eaee82f71af3e362906149e5c81c40e6ff5ec430e00a1bf7b923c` |
| context | context_unchanged | Will NVIDIA (NVDA) hit (LOW) $176 in October? [market=4935844; condition=0xdbc466fb9969f8e659a19bb5b9e253c1cea1250ec2e7699dc3a769f08871e821] | Yes=0.0235, No=0.9765 |  | True | `d290c7bd6a16752b21adb0b54bb167e2672a285c4fffbdf680eb0672e7ba16ce` |
| context | context_unchanged | Will NVIDIA (NVDA) hit (HIGH) $232 in October? [market=5465162; condition=0xa6a153f1bbbc734c90c47c14e49c392e0a8212d95805b448164f74b07c1fd39d] | Yes=0.315, No=0.685 |  | True | `f290677e7a7922d48929171ea25515eb05ea1ddfd8f99bd9ab8d4315a58fa592` |

## Batch 16 (20 markets)

### Which company has #1 AI model end of October? (Style Control On)
Group basis: `exact_gamma_event_id`; event ID: `841241`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 87 | new_to_snapshot | Will Meta have the #1 AI model at the end of October 2026? [market=3554763; condition=0x80a9ba0f4f84317f73c540f6a618dfb21ef0209d568d6aed49b05e08add59c16] | Yes=0.032, No=0.968 | new_to_snapshot | True | `dc2d9b9459a58c8b3696b6c98a61903e9dc4f1625c1904b9fccc9d8e8d9bc5ab` |
| 209 | changed | Will Anthropic have the #1 AI model at the end of October 2026? [market=3554762; condition=0x6bfaafe05727cfb17e52bd8e983a26e54d622968fb854f1bb9fd28bbdec0b63e] | Yes=0.1875, No=0.8125 | best_ask, best_bid, no_price, yes_price, outcome_prices | True | `d7df19fe99243591fd4e8725c96e09b2fbf819716b7124600b62519946f7f049` |
| 227 | changed | Will Google have the #1 AI model at the end of October 2026? [market=3554764; condition=0x87ac99fe038a2c345150cc4ba5a641ec823c52e532f5d9f06b64286149f787de] | Yes=0.735, No=0.265 | best_bid, spread | True | `98735830517dd9df11f297fcc3d790e4353560632b11497373d730c5911932ea` |

### Delaware Senate Election: Turnout
Group basis: `exact_gamma_event_id`; event ID: `870828`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 88 | new_to_snapshot | Will total votes cast in the 2026 midterm election for Senator from Delaware be between 375,000 and 400,000? [market=3697359; condition=0x633343039d1f01cbf9d1946286d61caff7423fe5600ce8aec7e319cbcfab21cf] | Yes=0.2995, No=0.7005 | new_to_snapshot | True | `5bc07780e9539aa8c52c2d776e958807fcabe0e39b3c5200861874eb9ee1effe` |
| context | context_unchanged | Will total votes cast in the 2026 midterm election for Senator from Delaware be between 400,000 and 425,000? [market=3697360; condition=0x4f0688dd613f1d5213848c0e0ca28b01cd77f7354e79af6ea4d20f611e399bf3] | Yes=0.15, No=0.85 |  | True | `bda4c6e38c05f2b9726105f7ac273f2f2027726117cd1314ece4c3fa005dd17a` |

### What will Amazon.com, Inc. (AMZN) hit in October 2026?
Group basis: `exact_gamma_event_id`; event ID: `1078032`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 89 | new_to_snapshot | Will Amazon.com, Inc. (AMZN) hit (HIGH) $304 in October? [market=4935757; condition=0x7f8098c5ab6a8c446318ba8ca3026c34c733844a283d8c8e8872d4be69633aa0] | Yes=0.1145, No=0.8855 | new_to_snapshot | True | `9a4387f6504c85cf3b2be18ecfbc6d5a42f82d74b0312e28e90740581c5e6276` |
| 100 | new_to_snapshot | Will Amazon.com, Inc. (AMZN) hit (LOW) $224 in October? [market=4935775; condition=0xd9f9029844f497fd9205525a09df27b095b1599a101e3fbdf8e1fbd28c23e70b] | Yes=0.13, No=0.87 | new_to_snapshot | True | `eb25a4a5be2056c140f7b7c444b0ac979b1b8360b162e8fff2a2b408efcea065` |
| 221 | changed | Will Amazon.com, Inc. (AMZN) hit (LOW) $216 in October? [market=4935776; condition=0x898fd1c3fff7cdc2a56251086705c439c22ead8b7ef883adfe92d05671e1d892] | Yes=0.065, No=0.935 | best_bid, spread | True | `e73854386f76bcca30569976b88492c2ade23c4533c2760580c88d8ffca4ae5c` |
| context | context_unchanged | Will Amazon.com, Inc. (AMZN) hit (LOW) $208 in October? [market=4935777; condition=0x8a55d447aaa1fe69953dc5a192ec5c164fa9faf855107fed0f95f5c3b73f0288] | Yes=0.0415, No=0.9585 |  | True | `c5f023fc4588f257273d2821fb5d88c24ca2f60eaeaaaeeb19a544f1bf0bb751` |

### Second-best Text Arena Math AI Lab end of October?
Group basis: `exact_gamma_event_id`; event ID: `841207`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 90 | new_to_snapshot | Will Anthropic be the second-best Math AI lab at the end of October 2026? [market=3554403; condition=0x5c752219b737d9c64dfe3b6d6925c062beb139671e400cf1dddaaf7028779eeb] | Yes=0.505, No=0.495 | new_to_snapshot | True | `a96d06cbcaa717a55e576df86d15d883379ff00dc6b6fcf8e75d14208586cfc0` |
| context | context_unchanged | Will Google be the second-best Math AI lab at the end of October 2026? [market=3554404; condition=0x4229c383fa8cd43a052c57b261c04accfccacef3980175859b7786729d43a62a] | Yes=0.405, No=0.595 |  | True | `63b70b3aa778f621eec7ca1274a8b745b099d141820601e3ae3d6b6b62037b46` |

### NV-03 House Election Margin of Victory
Group basis: `exact_gamma_event_id`; event ID: `834412`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 92 | new_to_snapshot | Will the Democratic Party candidate win the 2026 NV-03 House election by 10%-15%? [market=3519879; condition=0xbb32b87fc60445e05d48c720ef73a66197582553f5aa50bf836fed33a2051341] | Yes=0.215, No=0.785 | new_to_snapshot | True | `59f5cbcb84d127f7c809864de5a9350f4585c1ba7e8656dad8966d1dffe1c236` |
| 175 | new_to_snapshot | Will the Democratic Party candidate win the 2026 NV-03 House election by 20%-25%? [market=3519877; condition=0x59fd77309b592ba2435e8547c484d24417df6c3d2c44c9a2e19142efc2a0f6bb] | Yes=0.07, No=0.93 | new_to_snapshot | True | `958b6e937adcd84f8378589d1c6734f9e098795be1caa83cb4dd365741864fae` |

### NCAA Football: Team to Make National Championship
Group basis: `exact_gamma_event_id`; event ID: `801515`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 93 | new_to_snapshot | Will South Carolina Make the 2027 College Football Playoff National Championship Game? [market=3361069; condition=0xa6d4b8eb368ed99d2bfcc57bf7abccfa070eac4e06ecc0f0b2a82b3c0b31ca8e] | Yes=0.0365, No=0.9635 | new_to_snapshot | True | `db4f2f50c09a1feff8c586fa5f226dc7e4750515d9812e4855ab4c78f579a620` |
| context | context_unchanged | Will BYU Make the 2027 College Football Playoff National Championship Game? [market=3361055; condition=0x646d6d1ce605480f5bdcb69c9aade39bb40823457b58e7f32275c3f29257236f] | Yes=0.085, No=0.915 |  | True | `da04d59ed1126572f814f0bf48aa0760ac7ed5d15f99e52d0791f469417a33ec` |
| context | context_unchanged | Will Louisville Make the 2027 College Football Playoff National Championship Game? [market=3361066; condition=0xab5132ce5bd6bc1f38d53cc9aba992bc4490e9863e48bb30543cf956b26d204f] | Yes=0.0315, No=0.9685 |  | True | `c8b2cf2d9b785555de626030b693b9d76369eba241d6e804335cbf437a028cd1` |
| context | context_unchanged | Will TCU Make the 2027 College Football Playoff National Championship Game? [market=3361076; condition=0x579ac64f64f7b420ed947070fb969b47fb33b8e8b117434e9233abbddbfa969c] | Yes=0.04, No=0.96 |  | True | `c8b7da7ca3a6fb047d095898526a615af37e2ce0edf6a23aadd348e617116aa5` |
| context | context_unchanged | Will Florida St. Make the 2027 College Football Playoff National Championship Game? [market=3361089; condition=0xeaedf027b923518d1a6a188d3eb4263acb9463778567715eaa7b4cb9feabd3f2] | Yes=0.031, No=0.969 |  | True | `73752f6e8991b05a87ddcbd9b087558148f7b87eed172ab4e54d6db975481495` |

### Next Israeli Minister of Interior?
Group basis: `exact_gamma_event_id`; event ID: `1107823`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 94 | new_to_snapshot | Will no next Israeli Minister of Interior be appointed by February 28, 2027? [market=5151815; condition=0x84183fca786cd364abf470fa01b8d547671a63844e0d606d55c775f9e84e839b] | Yes=0.28, No=0.72 | new_to_snapshot | True | `310dcc6c646f1570c2ba824e838ef4dfd228e4e18d4e9bbefc2430f5fbbd1ccc` |
| 138 | new_to_snapshot | Will Michael Malchieli be the next Israeli Minister of Interior? [market=5151797; condition=0xc9735f35bbde76417cb5de68d0f3ead41a4cbe5a2fa5615f14e18da844f8cf93] | Yes=0.045, No=0.955 | new_to_snapshot | True | `9889359820265158f48448581fa01500f8e26924606f677ec787d1d1abdc5194` |

## Batch 17 (18 markets)

### OR-02 House Election Margin of Victory
Group basis: `exact_gamma_event_id`; event ID: `834477`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 97 | new_to_snapshot | Will the Republican Party candidate win the 2026 OR-02 House election by 25%-30%? [market=3520412; condition=0x59445bd2835ecfbad469994e5fa56476b0e9bb643a65c02b071e8df0fd2d1410] | Yes=0.2645, No=0.7355 | new_to_snapshot | True | `82796fceeaa578a828ac6f283c005d61aaf4e80a5eba503f752473963a264b77` |
| 169 | new_to_snapshot | Will the Republican Party candidate win the 2026 OR-02 House election by 15%-20%? [market=3520414; condition=0xf9220a02faa4e862bdb60451a9c5a5f5049bb129de7f0c22ece7d8fe793224be] | Yes=0.305, No=0.695 | new_to_snapshot | True | `27289e35775926850d238e3ae692818041a8245c6082528f028f05d9c9ebf813` |
| 178 | new_to_snapshot | Will the Republican Party candidate win the 2026 OR-02 House election by 20%-25%? [market=3520413; condition=0x353bf8de26d74d55bba0b39a9c96925a90582d83ffb20e1b986e729504841daa] | Yes=0.345, No=0.655 | new_to_snapshot | True | `6c816995e58ff7aaae79dace54fdc7a7db1a00ce1731fd174656bd6a191407db` |

### NC-01 House Election Margin of Victory
Group basis: `exact_gamma_event_id`; event ID: `834098`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 98 | new_to_snapshot | Will the Democratic Party candidate win the 2026 NC-01 House election by 0%-3%? [market=3518534; condition=0x4541cf1a54237059028c1010e91b1d64c6b2a5e19f9e571a1723d9e68ac90462] | Yes=0.19, No=0.81 | new_to_snapshot | True | `4110d4c47564e54d8ce80787b37dcf57223ade80783929c7a40af73ca42f6e26` |

### Israel Election: Yisrael Beiteinu # of seats?
Group basis: `exact_gamma_event_id`; event ID: `966892`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 102 | new_to_snapshot | Will Yisrael Beiteinu win 6-7 seats in the 2026 Knesset elections? [market=4232148; condition=0xf76db9fd1162c60eea449dfa2047c347c36eae3cdd67d86f1bc6148a6706f7f7] | Yes=0.225, No=0.775 | new_to_snapshot | True | `80acea7fb3cd49918f5d41d6ef7b07f971cac6284ebd4f02d31951efa2e857e1` |

### NY-01 House Election Margin of Victory
Group basis: `exact_gamma_event_id`; event ID: `834410`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 103 | new_to_snapshot | Will the Democratic Party candidate win the 2026 NY-01 House election by 3%-6%? [market=3519860; condition=0xa684d239df8ab692ceff17398ae2d51e15025239978f578f207ad6172fa84216] | Yes=0.028, No=0.972 | new_to_snapshot | True | `5d161fa667cb70ee03f2690f6ff455b8480df72acec84edb3e1b23662836a8e0` |
| context | context_unchanged | Will the Republican Party candidate win the 2026 NY-01 House election by 18% or more? [market=3519852; condition=0x6d035dc7b2274eca16c03a522263601eb614c1cc09708e751d86ef874c7385fc] | Yes=0.0685, No=0.9315 |  | True | `f19c2fe31f65a3e7bffe6d05cd8335e39a66103894d6e14e6fdabe6d0f0af356` |
| context | context_unchanged | Will the Republican Party candidate win the 2026 NY-01 House election by 15%-18%? [market=3519853; condition=0xfe8cb1681a0bae065914a2c9103fd3b6c5eb6a71e2b2218cbfb05f90a0a2bfa4] | Yes=0.046, No=0.954 |  | True | `c90c602b650108b34b68e2955fe6eb0b927c4659f54f49e1a336363fc26fdbb7` |
| context | context_unchanged | Will the Republican Party candidate win the 2026 NY-01 House election by 12%-15%? [market=3519854; condition=0x59d1ed19fb8b2dcfbb8b42faeb8e64ea045ba85886ebfb510caf099d15a3c1ec] | Yes=0.093, No=0.907 |  | True | `b3d3dccb7db65690d4bba9748182d01947ace9d1de1fa974c71ad64d27de5133` |
| context | context_unchanged | Will the Republican Party candidate win the 2026 NY-01 House election by 9%-12%? [market=3519855; condition=0xa56b7153ded1877146483e0e39099c64d3f9623cfb035fbab70b09974c798927] | Yes=0.105, No=0.895 |  | True | `76e378d6635941385ea7bc1002eb9864b68e5c2fac0b18f2c980baa95940e443` |
| context | context_unchanged | Will the Republican Party candidate win the 2026 NY-01 House election by 6%-9%? [market=3519856; condition=0x4a7967ba654a34aa2b494c989a8e80c8649f2f23bc8b8b68c034ee2142680643] | Yes=0.115, No=0.885 |  | True | `0cab8572e8da20c12fdcfdb82427a7fce1eaeafecb87bc4d03d7791440cbf317` |
| context | context_unchanged | Will the Republican Party candidate win the 2026 NY-01 House election by 3%-6%? [market=3519857; condition=0xad096dc27f599f370088c69325a1b42276dd1e1a8253c98d6bf958c10e743af8] | Yes=0.1845, No=0.8155 |  | True | `22da8a680d2bbde56be51fddc1a058236a289adda79a7ffd9396503e65d2937a` |
| context | context_unchanged | Will the Republican Party candidate win the 2026 NY-01 House election by 0%-3%? [market=3519858; condition=0xce12ee4767ad7eba29a2b388af6858eabcc3b63d2442971634649d86404364ef] | Yes=0.2, No=0.8 |  | True | `a5f2090edd56182d4ce023bf81c6005a156baee0834f111a423d7d024989b47d` |
| context | context_unchanged | Will the Democratic Party candidate win the 2026 NY-01 House election by 0%-3%? [market=3519859; condition=0xb42738b534336e50a977119a3e8516b72a40117453c37589ed6b27d0090a890f] | Yes=0.152, No=0.848 |  | True | `cf4037ccdd9dddb39dab724f3c75a54369565f1526cb495ba492b1abe1d9d9d1` |
| context | context_unchanged | Will the Democratic Party candidate win the 2026 NY-01 House election by 6% or more? [market=3519861; condition=0xf3b3d0b5d91302dd9688a962667c202001027e13ead0ad375ad494e9f147ffbd] | Yes=0.04, No=0.96 |  | True | `c4369e7cfca6fbce444ab61a289e029e5e1cd68e87de4c88a832b9920dce60a4` |

### Second-Best Chinese AI Company end of October?
Group basis: `exact_gamma_event_id`; event ID: `841210`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 104 | new_to_snapshot | Will Alibaba be the second-best Chinese AI company at the end of October 2026? [market=3554496; condition=0xca6570facc10e587699c442db1452d30dece93314737e9b5eda027a660f2bdc4] | Yes=0.435, No=0.565 | new_to_snapshot | True | `d9c666fef8a417b42025fac9fb5ac632722bddcb68e150162b8dcd513ddfa79c` |
| 145 | new_to_snapshot | Will ByteDance be the second-best Chinese AI company at the end of October 2026? [market=3554502; condition=0x32efa72cda512864a43e272ed4352916cc5ab9475e63b999e2e388402b1606b9] | Yes=0.0065, No=0.9935 | new_to_snapshot | True | `6345540caaafe760a3747c0d6f6671166fde0d84aefe8b93a55b445d5d7a4926` |
| 182 | new_to_snapshot | Will Z.ai be the second-best Chinese AI company at the end of October 2026? [market=3554499; condition=0xf61fc1459af53772933655e487e827bd4433a952bbdec50f10f428e5a5d0bdd9] | Yes=0.085, No=0.915 | new_to_snapshot | True | `938f42ddfa27dcfddf04dedcb38bc842ca8ee2e21a8086cdcde816dcf261a0a0` |

## Batch 18 (20 markets)

### Oscars 2027: Best International Feature Film Nominations
Group basis: `exact_gamma_event_id`; event ID: `1193376`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 105 | new_to_snapshot | Will "Fjord" be nominated for Best International Feature Film at the 99th Academy Awards? [market=5725923; condition=0x9855e508084c8710105c913c831f78ac2932ee59ac238a436c80dad6fd6abaf6] | Yes=0.745, No=0.255 | new_to_snapshot | True | `1def071da61dcf0f9bebfc14a9617699955445752df6589f83ee3f25ef2c3545` |
| context | context_unchanged | Will "The Black Ball" be nominated for Best International Feature Film at the 99th Academy Awards? [market=5725921; condition=0x9bb328594ec298602b11c36d14a4d6408db39d73cc68d91691f3613a6a16c249] | Yes=0.945, No=0.055 |  | True | `5b1c86940d123f29af294ce3631721d5082a657a1ec13be120c9504be3bc3062` |
| context | context_unchanged | Will "All of a Sudden" be nominated for Best International Feature Film at the 99th Academy Awards? [market=5725922; condition=0xf917db0fadc04970b1bfc0719d7a12f46ecbafd3e0c2176bd284f8a407f6193c] | Yes=0.825, No=0.175 |  | True | `e9e9f85ba246cc4911883cf08261c28fae32bedf554bacd5ccdc350d3a7a8173` |

### What will SpaceX (SPCX) hit Week of October 19 2026?
Group basis: `exact_gamma_event_id`; event ID: `1202046`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 106 | new_to_snapshot | Will SpaceX (SPCX) hit (LOW) $137.50 Week of October 19 2026? [market=5789107; condition=0xecc6568c7fd25785d5e304be3bb51b8890e8869ef96a55d99dced111caec1234] | Yes=0.385, No=0.615 | new_to_snapshot | True | `f641af4df45f711609a17fcd135f9ffb4100186cc17881246bc914d912b8067a` |
| context | context_unchanged | Will SpaceX (SPCX) hit (HIGH) $162.50 Week of October 19 2026? [market=5789097; condition=0x708eef7ba607fc302fb262d4801f9ede3a95a47070cca78529a8f54df1dd6c35] | Yes=0.325, No=0.675 |  | True | `33c08129459e7f78ba0813f99510f98add9936ec3a7795df659a97f3888b6c8a` |

### MI-03 House Election Margin of Victory
Group basis: `exact_gamma_event_id`; event ID: `828347`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 107 | new_to_snapshot | Will the Democratic Party candidate win the 2026 MI-03 House election by 30%-35%? [market=3491647; condition=0x8a47d5faeee18e36d447f010d8ddafb0dd8e3149e26dbd14460c0d5c6a38c7fa] | Yes=0.0055, No=0.9945 | new_to_snapshot | True | `312918e89d4c1f1978b682ba1b385435159beb5463ac27cc27c84acedf4915fa` |
| context | context_unchanged | Will the Democratic Party candidate win the 2026 MI-03 House election by 20%-25%? [market=3491649; condition=0x74913632f7428a9cd92c3825f70f9cab406908711cd389cb425d710d1291e192] | Yes=0.215, No=0.785 |  | True | `d9e56d23b2416679b41161de89cd9a789755a37311c98a36d93a34758d6ed68c` |
| context | context_unchanged | Will the Democratic Party candidate win the 2026 MI-03 House election by 15%-20%? [market=3491650; condition=0xc07b35826f18000a2233ad24bcc83519ee7f17499df75ae1c2984bcc7d414124] | Yes=0.21, No=0.79 |  | True | `6c134c9f3d02c09eacecc2c62d377fd29968a42d824da0785142bb75e3940b9c` |
| context | context_unchanged | Will the Democratic Party candidate win the 2026 MI-03 House election by 10%-15%? [market=3491651; condition=0x3e98805249c867d79529360c691c15e0229e7c4904644fa751fe0bce019e43f8] | Yes=0.23, No=0.77 |  | True | `1bf2dc625ef650064436bc379fc21357210df3474023ad93eec143b2ad9790d3` |
| context | context_unchanged | Will the Democratic Party candidate win the 2026 MI-03 House election by 5%-10%? [market=3491652; condition=0x042cf19f640f6d8e73fc12dc471c9b87664e7150cc81e7852ed98ef6d35ca86e] | Yes=0.017, No=0.983 |  | True | `6b9663178929d995a876efcc472c948b9202a8888331fd00db95ecbd2baf012f` |

### GA-02 House Election Margin of Victory (First Round)
Group basis: `exact_gamma_event_id`; event ID: `812680`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 108 | new_to_snapshot | Will the Democratic Party candidate win the 2026 GA-02 House election by 25%-30%? [market=3408859; condition=0xce1363ee953b23aab6b676d100743acb04b82dbade9906c6f9d840ccabe770d6] | Yes=0.1885, No=0.8115 | new_to_snapshot | True | `d97b4dba64ce0aa1478822f725b88bd30113d851008f6796b0ddf01cc32c9156` |
| context | context_unchanged | Will the Democratic Party candidate win the 2026 GA-02 House election by 20%-25%? [market=3408860; condition=0x2344748e557365497086e61009a874ad46a19f9604fc1da761307ae63f209a11] | Yes=0.36, No=0.64 |  | True | `a9b198d87f01f30bb007493b771015385525c85cba69a985a6a4a44d57c39ea1` |

### Ohio Senate Election: Mahoning County Winner
Group basis: `exact_gamma_event_id`; event ID: `1099774`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 113 | new_to_snapshot | Will the Democrats win Mahoning County in the Ohio Senate race in 2026? [market=5091119; condition=0xf177376cf64c5aa76e7e25e4bec67acbb7530785f29c7c03589d221adbca0f85] | Yes=0.7, No=0.3 | new_to_snapshot | True | `d6c245f140d363db310a39a20a5c329090fede91364852f0191cf47086c110b4` |
| context | context_unchanged | Will the Republicans win Mahoning County in the Ohio Senate race in 2026? [market=5091120; condition=0x665f82b9d8de4c9a44a95ebdbbaf27ab531ab9ab33dda74a557bc04d1085a303] | Yes=0.27, No=0.73 |  | True | `ca0dd091268bc379f73a134af1cfa2b859e0f67d00aa938614052133ccd2ce63` |

### What will Palantir Technologies Inc. (PLTR) hit in October 2026?
Group basis: `exact_gamma_event_id`; event ID: `1078040`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 114 | new_to_snapshot | Will Palantir Technologies Inc. (PLTR) hit (HIGH) $216 in October? [market=4935862; condition=0x04fdc5d5941042a07b73c04cba7c630935ec68a5f527fcdc454dd82ee1da2b17] | Yes=0.26, No=0.74 | new_to_snapshot | True | `0bf3149a32ec75eeed33270832bbaba0f60c7b5ae8c1acb00cee49c0f5c680fd` |
| context | context_unchanged | Will Palantir Technologies Inc. (PLTR) hit (LOW) $156 in October? [market=4935872; condition=0xba4a2f40e3a493776ef4fba33691b97a02e91008e79ebaf800f05c91b446acf8] | Yes=0.0425, No=0.9575 |  | True | `dd03befa129465abf574e81ba264e0903bbeada9b88a2ea8bca625ef068374e9` |

### What will Meta Platforms, Inc. (META) hit in October 2026?
Group basis: `exact_gamma_event_id`; event ID: `1078036`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 115 | new_to_snapshot | Will Meta Platforms, Inc. (META) hit (HIGH) $780 in October? [market=4935809; condition=0x0f5e0343a711af8d0b236e9ac59ac6264d8f8a74985d6c259966a4aa90ee6ec5] | Yes=0.28, No=0.72 | new_to_snapshot | True | `533ea9968b1b5aa02f855a5adefc30800a43dbc98b11e3962a121f811c5131ba` |
| context | context_unchanged | Will Meta Platforms, Inc. (META) hit (LOW) $680 in October? [market=4935814; condition=0xf2bdff8305a44a023b6ab53bf7348f379f4ea7eeea14550e209ec9c5e5f20b2e] | Yes=0.695, No=0.305 |  | True | `7598618d7e36f49670a5aaa9cd6bd9304998271f6919fd5870ae37813bb5b42f` |
| context | context_unchanged | Will Meta Platforms, Inc. (META) hit (LOW) $600 in October? [market=5131531; condition=0xf3f1de698b504bdb14cff6ea9eb50dd4a79b0733a537b3c105e2e82481a1bf7f] | Yes=0.12, No=0.88 |  | True | `f70c3615a3be310b78087b421f7da498d62af686d2edaa9f30828bae1a2d4eaa` |
| context | context_unchanged | Will Meta Platforms, Inc. (META) hit (HIGH) $740 in October? [market=5778250; condition=0x077151a7f4feb471209a84a4409a0f50300936b341a07a12446aed78039bb525] | Yes=0.55, No=0.45 |  | True | `01a699aab4094c9052a21e73cf6b5717a58866a1419778ac587a383182928889` |

## Batch 19 (18 markets)

### Ballon d'Or 2026: 3rd Place
Group basis: `exact_gamma_event_id`; event ID: `1218179`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 116 | new_to_snapshot | Will Declan Rice finish 3rd in the 2026 Ballon d'Or? [market=5926215; condition=0x739c6fc9e3b03fd2e4fdbd05192e11c2ff64037aa3125a3fe8f6fe21bbea53a0] | Yes=0.045, No=0.955 | new_to_snapshot | True | `4428fe46a000888ac0f7d308a4e630a1a81a12e7265131b4434e6365238d89a7` |
| 117 | new_to_snapshot | Will Vinícius Júnior finish 3rd in the 2026 Ballon d'Or? [market=5926214; condition=0x7f4a97157c51517fc279a5d2552149f1746b1c211a69c46efcb540339bb8a03b] | Yes=0.02, No=0.98 | new_to_snapshot | True | `322ca350605e8b1706bb64b12a7b36ea91d303780b6fa84ef0a6b06011ef872b` |
| 118 | new_to_snapshot | Will Lautaro Martinez finish 3rd in the 2026 Ballon d'Or? [market=5926228; condition=0x063d64e9c9a2959a70bbcfb980e9565ecad9692545856a39bc1747e6cbaa8fe0] | Yes=0.04, No=0.96 | new_to_snapshot | True | `cf17039caa470195b2016abf666a162c2d3775061690d4a746d445525efac23a` |
| 202 | changed | Will Lamine Yamal finish 3rd in the 2026 Ballon d'Or? [market=5926203; condition=0x1864c9203cec26f0b34d747a69170a7e66e7084d740d52a53e80f857811c9875] | Yes=0.545, No=0.455 | best_ask, best_bid, no_price, yes_price, outcome_prices | True | `f597022d79b2e64d59f99b36488a57e566e559dc39bf46ba198883fa8868d424` |

### What will Robinhood Markets, Inc. (HOOD) hit in October 2026?
Group basis: `exact_gamma_event_id`; event ID: `1078045`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 120 | new_to_snapshot | Will Robinhood Markets, Inc. (HOOD) hit (LOW) $90 in October? [market=4935971; condition=0x68f6eec62fa1713e84d3d7c9b833b1211b771f16d6954a76e3c5e1eb7dd0b534] | Yes=0.485, No=0.515 | new_to_snapshot | True | `bd01a104cff0b3a886c1e42ac02e469225d1960250d44e6cfd451fad0043eefa` |

### What will Gold (XAUUSD) hit in October 2026?
Group basis: `exact_gamma_event_id`; event ID: `1078053`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 121 | new_to_snapshot | Will Gold (XAUUSD) hit (LOW) $4,100 in October? [market=5743134; condition=0xaebe4226ed73f30c7ae1135b978cc3949c245dae6a70a8a7a9241408072cbd3d] | Yes=0.775, No=0.225 | new_to_snapshot | True | `4e6556e2041e7c24cfbbfac9c4eb73e8fc9a4f781848b56d06b37535187edb56` |
| 207 | changed | Will Gold (XAUUSD) hit (HIGH) $4,300 in October? [market=4936076; condition=0x10daf016e313293b6a15086e9b04fb1281cd88afc21fc2a782ad475c465601a4] | Yes=0.3, No=0.7 | best_ask, best_bid, no_price, yes_price, outcome_prices | True | `3a277301d415d51edef48656c0bbe1774dd5cab2a4cc7db815acad30952ca7bc` |
| context | context_unchanged | Will Gold (XAUUSD) hit (HIGH) $4,900 in October? [market=4936070; condition=0xd439614bddd29aa7a41baa210f97cf3b528d63754c23e1e9a7e32e848baa2c3b] | Yes=0.0065, No=0.9935 |  | True | `a8dfd9543c426c7de847e4269e9df596fc088f077342c1ea9b2e799811c81ff8` |
| context | context_unchanged | Will Gold (XAUUSD) hit (HIGH) $4,800 in October? [market=4936071; condition=0xa7439690916c2e7b65df192200349e6b0d4aae4b57d57dcc531e27015652a1ba] | Yes=0.008, No=0.992 |  | True | `6f44b72a212ebd5fdec7ff7c16decadb652ab96ef81f561438d55660813d63ba` |
| context | context_unchanged | Will Gold (XAUUSD) hit (HIGH) $4,700 in October? [market=4936072; condition=0xf075c059a3eda088aa5ef044d741ea01669924a9da66592aa0dad9dc4ebb4c5c] | Yes=0.0055, No=0.9945 |  | True | `2389dbaff3e01ca949667a818ede3eac9dddab46f8c0e0bfa6a8f9d97444cdba` |
| context | context_unchanged | Will Gold (XAUUSD) hit (HIGH) $4,600 in October? [market=4936073; condition=0x69f7c3581dbd712519dc371121614040da3f19c1d1994bd6ec1d2208a5b3ea86] | Yes=0.019, No=0.981 |  | True | `7b5f188b80014afbd0f10fd8a6b53ba2f08b1bf8678cbbfee14a31cbe5cd16b0` |
| context | context_unchanged | Will Gold (XAUUSD) hit (HIGH) $4,500 in October? [market=4936074; condition=0xf4f79d912087967dea3126bbec1760b1e872de12f47d8e40b6406470453556a6] | Yes=0.05, No=0.95 |  | True | `1f24675de37bbc7229a8d5f547c484739c24a77ab0e8ec5b17f21cd2f3fa6038` |
| context | context_unchanged | Will Gold (XAUUSD) hit (HIGH) $4,400 in October? [market=4936075; condition=0xa89593ff8b13b5fdf0b0ab2e188c151ebf14b650f6a9e36f9d8e2706121f4678] | Yes=0.1, No=0.9 |  | True | `85a64a9eca994b802951ced220bc045f2e8934b7e7ed9e57a558883f67c8536b` |
| context | context_unchanged | Will Gold (XAUUSD) hit (LOW) $4,000 in October? [market=4936079; condition=0xa3a2bf0cf7a8e639401b40de5ddb93049446673c2c75d03845d81fd3375efc82] | Yes=0.35, No=0.65 |  | True | `22a2771dcf38d75a68d82dbb71817bf28d5252f1ce646a3148603251fcac3140` |
| context | context_unchanged | Will Gold (XAUUSD) hit (LOW) $3,900 in October? [market=4936080; condition=0xdbcce974fd7d4a89d0fe383c25399ea5a8054381a3ff53d4fa3fd423fac383be] | Yes=0.11, No=0.89 |  | True | `a7250dd6c4a47cd538da0dece563c10e15299831fbeeeb81734a4920b27c98d9` |
| context | context_unchanged | Will Gold (XAUUSD) hit (LOW) $3,800 in October? [market=4936081; condition=0x1cab04d0ecd92539f612aac4c31fcf741d2dbed1a9af69437d7d838bf7c4460f] | Yes=0.048, No=0.952 |  | True | `9a444205e6faba29c7de21e8a1e9c7f7df00f02a120b945e1e8ef84bb02ad51b` |
| context | context_unchanged | Will Gold (XAUUSD) hit (LOW) $3,700 in October? [market=4936082; condition=0x39324dc5818dd9ec34abbff73ebc0ca004b737d5a5fa4e951cee319a2841c772] | Yes=0.0145, No=0.9855 |  | True | `7c13f9c98456d6ad3e5b91603e75d93b912173d25464ed62df552b034f5be611` |
| context | context_unchanged | Will Gold (XAUUSD) hit (HIGH) $4,200 in October? [market=5660571; condition=0x198beddf8e0b8a798630e7fb8c97d9a208532260b6d65151cbfc6dee16b0d72e] | Yes=0.698, No=0.302 |  | True | `470feec3aa660177c89b0afb61d58a0e5cd18b9626eaf07c2b0fc7d7b930a647` |

## Batch 20 (17 markets)

### What will Opendoor Technologies Inc. (OPEN) hit Week of October 19 2026?
Group basis: `exact_gamma_event_id`; event ID: `1202034`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 122 | new_to_snapshot | Will Opendoor Technologies Inc. (OPEN) hit (HIGH) $2.50 Week of October 19 2026? [market=5788943; condition=0x9bcfd0b94f86d07206b6522819eb5bad7c4c24edb61c7ffa5769b0f11c8e33ce] | Yes=0.135, No=0.865 | new_to_snapshot | True | `3dae1864dc849d652795e6fd1dd1d7535009de2a3a85f436ecb8c6178b76c3e3` |
| context | context_unchanged | Will Opendoor Technologies Inc. (OPEN) hit (LOW) $1.00 Week of October 19 2026? [market=5788958; condition=0x4152c03651a661c00bd1173885c267863ef2a38b4085ecf60dc231a2db22fd19] | Yes=0.006, No=0.994 |  | True | `827b31a5f1a30ac89b1e3a9368995f56728718b0adc6bf397c25b16bfbaa3b38` |
| context | context_unchanged | Will Opendoor Technologies Inc. (OPEN) hit (LOW) $0.50 Week of October 19 2026? [market=5788964; condition=0xbef757d4031c5cec289f96329f725306a63484084cfba0f6b5276d7ab89ed745] | Yes=0.0045, No=0.9955 |  | True | `52ec6f8569f3c9a7b1744083ac6a1680ab50285156b7abcaae15a421ec0a17ec` |

### GA-08 House Election Margin of Victory (First Round)
Group basis: `exact_gamma_event_id`; event ID: `812694`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 123 | new_to_snapshot | Will the Republican Party candidate win the 2026 GA-08 House election by 20%-25%? [market=3408945; condition=0x6f1f6d8e9dd2e07d604bbef12a6ca8286d7641347f81f2d09642e6b9bf7b06b2] | Yes=0.205, No=0.795 | new_to_snapshot | True | `4bc261329dfee264ad5f2e29104227525e243c1f6b7177ed330d44a8ca7e5b65` |
| context | context_unchanged | Will the Republican Party candidate win the 2026 GA-08 House election by 40%-45%? [market=3408941; condition=0x1a551814263ea2c1b07b705bec986f62bf8fcdf61c1829a205a80f452e3dc01b] | Yes=0.027, No=0.973 |  | True | `f61ef13a3bbf5867c7ce6b971b430dc87594a1d6658d590d2cf73fd173c0648e` |
| context | context_unchanged | Will the Republican Party candidate win the 2026 GA-08 House election by 35%-40%? [market=3408942; condition=0xc7a0ea4ff8b1c21d6307661b55b61e483fe06fd87e932c107450888411a077b4] | Yes=0.0175, No=0.9825 |  | True | `6a7ea44e023a8832a8af8ecefa9aa1097fc3ec9b298705ee7a48df2fe9fc43bc` |
| context | context_unchanged | Will the Republican Party candidate win the 2026 GA-08 House election by 30%-35%? [market=3408943; condition=0x90333ff00481ec5111f15e434c1071e759cc7cf85d8a51f095de80b8492fd9d9] | Yes=0.19, No=0.81 |  | True | `8737f0347372ea35a06fcfc5411f2e59334e2bc9536ac3a477016ca56c18e445` |
| context | context_unchanged | Will the Republican Party candidate win the 2026 GA-08 House election by 25%-30%? [market=3408944; condition=0x1237b6a4a438ea79bdd3997d2c6bf9ff2df8b194ae11d26837e98f3fd2cde9c1] | Yes=0.32, No=0.68 |  | True | `7e1950226877ac544b332766a4b228c0200122d964c74d048414067496171fd4` |
| context | context_unchanged | Will the Republican Party candidate win the 2026 GA-08 House election by 15%-20%? [market=3408946; condition=0xd265c66a64fca8039b57b884fd46a4deb9d3ce656db2284af10d1324355a45ba] | Yes=0.1725, No=0.8275 |  | True | `426596696f1507d0ca312137b752bd9259101467c4b92c5650105d4f193e9222` |
| context | context_unchanged | Will the Democratic Party candidate win the 2026 GA-08 House election? [market=3408949; condition=0xeaeb653073d19a382cffa8401167be5af8c2751b8aada59c7c46e51c4e8320b5] | Yes=0.038, No=0.962 |  | True | `7bf9c27f9e79a2100856081c4a414b292ed5449c34ab38d9e388d74925197fda` |

### Prešov Mayoral Election Winner
Group basis: `exact_gamma_event_id`; event ID: `943065`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 125 | new_to_snapshot | Will Pavel Hagyari win the 2026 Prešov mayoral election? [market=4037955; condition=0x74ab4fedde41ccfe799d4bb5fa963941af8a20e31281751ccc736f4e5915c37e] | Yes=0.0455, No=0.9545 | new_to_snapshot | True | `70b7c83d19a784863953d9031522745d56e7af861e7b6e725141efaa857e7cc2` |
| 148 | new_to_snapshot | Will Artúr Benes win the 2026 Prešov mayoral election? [market=4037958; condition=0xe6164efb6ade6a0c337244b0a1729ec6add5aa7821b4bab2def2b857ae4c6570] | Yes=0.012, No=0.988 | new_to_snapshot | True | `a617335279548a90acc0d7c6f3753f3c834ab453985d061dea8f471acef88580` |
| 149 | new_to_snapshot | Will Martin Eštočák win the 2026 Prešov mayoral election? [market=4037957; condition=0x5698ed7df3faaf6dd4f887deedce1a671a9cce9e5d3366b08e701f0c9706998c] | Yes=0.0235, No=0.9765 | new_to_snapshot | True | `50e94a639abdd04202cb41d023d68ec45cd89c0f4fff4ac0ba2968d64a2c9d13` |

### Oscars 2027: Best Production Design Winner
Group basis: `exact_gamma_event_id`; event ID: `1188339`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 126 | new_to_snapshot | Will Wildwood win Best Production Design at the 99th Academy Awards? [market=5686489; condition=0x111d14a5221615c4f20c61834cd8a16dfb3060d94fcd1c2f6ccc42c4822bafbf] | Yes=0.0495, No=0.9505 | new_to_snapshot | True | `7b34c9e9104ccb7b051e7064e45c284f8def94ddabce9c497476d7dac713c540` |
| 151 | new_to_snapshot | Will Digger win Best Production Design at the 99th Academy Awards? [market=5686483; condition=0xbee5315bb12f2076e5f0f169a947e46f085359b55a428f7c69ed6e27230ac284] | Yes=0.1605, No=0.8395 | new_to_snapshot | True | `0c2fd917d9a123adeee8b4c53a68c245430e8a7b0be7c91d08904a3e610f6a7f` |
| 172 | new_to_snapshot | Will The Odyssey win Best Production Design at the 99th Academy Awards? [market=5686478; condition=0x8c6d7234265a78cd9ef6b2d2885442a9ba2bb9eb35ce46e26884048d1a77935c] | Yes=0.555, No=0.445 | new_to_snapshot | True | `ee04c8a20ee2140005cdba64f81fc9fded1c91b71d0f09cde2c9834d0b64e7bb` |
| context | context_unchanged | Will Dune: Part Three win Best Production Design at the 99th Academy Awards? [market=5686481; condition=0xee41ebdc149a36051381e715ede34f4c99e623c502237657a73e29d9f8218d44] | Yes=0.22, No=0.78 |  | True | `f3e4a0dfdb0ea0c2f67ce19a4516223d42d2086faff60248a057e8400602cb78` |

## Batch 21 (16 markets)

### # of ChatGPT Outage Days in October 2026?
Group basis: `exact_gamma_event_id`; event ID: `1108499`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 128 | new_to_snapshot | Will there be exactly 3 ChatGPT outages in October 2026? [market=5154279; condition=0xd082492fc2bf90343bb9dedcac19e149451ccbbb648fc88cd8020508d5093675] | Yes=0.0055, No=0.9945 | new_to_snapshot | True | `e9c1fd3f8bab035ab53b7cc0e7bf3840978165d5793cb7da7196bb990c3a0e78` |
| 140 | new_to_snapshot | Will there be fewer than 1 ChatGPT outage in October 2026? [market=5154276; condition=0xc8defef06763e0588b92c2e383cc69b9379cbf65838c19cdc13bd264cd9fcffe] | Yes=0.007, No=0.993 | new_to_snapshot | True | `ccbc9917b99e5898b59924b98659575a48747919d05f08b69d73441e263b8c74` |
| context | context_unchanged | Will there be exactly 1 ChatGPT outage in October 2026? [market=5154277; condition=0xf5a9385752d7157dc374ff1c3a8d99f657ed59941de060fa945e4ce144766465] | Yes=0.0045, No=0.9955 |  | True | `9e4dfc1f6088018d8af3de7be01b5ad3222e3a5ad2f96d2f219bb11ae3c983d8` |
| context | context_unchanged | Will there be exactly 2 ChatGPT outages in October 2026? [market=5154278; condition=0xdf98a0980f8a29f3ddf59cb741f7303399b11a7ba05b206b4dabefc60217ccb6] | Yes=0.014, No=0.986 |  | True | `96c4209020a3d660fb46ac917aa583a82789fe8d2a7c094abc8b495d9a3d1b60` |
| context | context_unchanged | Will there be exactly 4 ChatGPT outages in October 2026? [market=5154280; condition=0x64b5ef8f8c2069dbcb5377ba2f72a65faa34b8ef0fa256ed6ecdbfce28b2a144] | Yes=0.167, No=0.833 |  | True | `8631ca1c41823a1fb829c3a90432e52c7ece6002eab13e53e17e1d6e6f27d462` |
| context | context_unchanged | Will there be 5 or more ChatGPT outages in October 2026? [market=5154281; condition=0xb2e78d013f958a9ccf2ec2bfb85ddf3fe3882e4a548dfd95a239d018eab702c7] | Yes=0.765, No=0.235 |  | True | `6608ebf5de4316876c5b9243af35abaac813aecad907a2ff3847ec87840282fd` |

### Michigan Senate Election: Turnout
Group basis: `exact_gamma_event_id`; event ID: `870865`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 129 | new_to_snapshot | Will total votes cast in the 2026 midterm election for Senator from Michigan be between 4,600,000 and 4,800,000? [market=3697489; condition=0xd788324a006ccd4ceff0042f9c6915a5c9d53d14b8bd32c15084a5f199d5961a] | Yes=0.28, No=0.72 | new_to_snapshot | True | `398a80c40153d61f4bc00a3108103d8fc24354a9dee9b243bf3db9f61e6d380b` |

### IL-07 House Election Margin of Victory
Group basis: `exact_gamma_event_id`; event ID: `828087`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 130 | new_to_snapshot | Will the Democratic Party candidate win the 2026 IL-07 House election by 70%-75%? [market=3488488; condition=0x7b902108f8008b0218b068f6eced14ef4d98d81061308c19663209b9e243b9b5] | Yes=0.232, No=0.768 | new_to_snapshot | True | `575a6aa7177f5e039d90e1875a2c6eed2363dd5b26989c053f3d52641de07a3c` |
| 134 | new_to_snapshot | Will the Democratic Party candidate win the 2026 IL-07 House election by 60%-65%? [market=3488490; condition=0x0a3808197730f1e2969b33bbd9953f7baefb025d257c6e6edbeaed7fa942c898] | Yes=0.161, No=0.839 | new_to_snapshot | True | `4ebef7db44b51364dbc8c8be00100a1c7543e180989f0e2464204ae11ba2986b` |
| context | context_unchanged | Will the Democratic Party candidate win the 2026 IL-07 House election by 65%-70%? [market=3488489; condition=0x750ce9d649a1a1ba42f78b85f3cdb99099f16a98d217f168080638cd09376806] | Yes=0.305, No=0.695 |  | True | `bdd36ba9973a879c3d4457cab6fcf70c3ca727f39f3336b0fe3e1ac4f1f5e66f` |
| context | context_unchanged | Will the Democratic Party candidate win the 2026 IL-07 House election by 55%-60%? [market=3488491; condition=0xa4415efdc689152cd4ed1d11d915b4028ffbc842ca755016e932baa4dc0326c1] | Yes=0.045, No=0.955 |  | True | `2dc2f355d36ff08c426b5446a6aa7f8f4e75eccd1b5bcee50a4b6d0d3c6e1d22` |
| context | context_unchanged | Will the Democratic Party candidate win the 2026 IL-07 House election by 45%-55%? [market=3488492; condition=0xf34b2a9b21ed663d2a6236b6572f524a2e358b3592e42ebf0ce8e2f1c58bb040] | Yes=0.04, No=0.96 |  | True | `50b65ed52704f77e468633bbace6e661757ade1795c97fa0b6e23ee91e8967bc` |
| context | context_unchanged | Will the Democratic Party candidate win the 2026 IL-07 House election by 0%-45%? [market=3488493; condition=0x9fb15c128515ccb72949c162d0fcbd347c5f9f12559e150a4b2aa4235f4fce3a] | Yes=0.004, No=0.996 |  | True | `0b8ac4a82e23f3e2885ef4e7fbd29f91cd12c9ac0d6a324d7f244b2dc05c8a2d` |

### OK-04 House Election Margin of Victory
Group basis: `exact_gamma_event_id`; event ID: `834474`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 131 | new_to_snapshot | Will the Republican Party candidate win the 2026 OK-04 House election by 35%-40%? [market=3520367; condition=0xab0ec980d6bb2e800ae48d6d01e898a737b0e42ddce8529411b1ae975ee337c3] | Yes=0.043, No=0.957 | new_to_snapshot | True | `c4047611585930aa67d6d7582156eea4896222a194148b2510a2925bdef7f050` |
| context | context_unchanged | Will the Republican Party candidate win the 2026 OK-04 House election by 25%-30%? [market=3520371; condition=0x520cbb30e16ea4c1ab1f80d19ebcc977d1d81e6f2aa664b9305d45b6708e4622] | Yes=0.21, No=0.79 |  | True | `0775cc6209e07f3310e06a8438c46f990a191dd27af2d83267deee83c820b849` |
| context | context_unchanged | Will the Republican Party candidate win the 2026 OK-04 House election by 20%-25%? [market=3520373; condition=0x838e331879cd4908240ecec4f557e6bc326f4616600c506f1c33bf557f50d350] | Yes=0.295, No=0.705 |  | True | `0288153bc2109a05e04817a9cdcdedd7b2060c99e2d92532a5d3bea4dc28520f` |

## Batch 22 (20 markets)

### Which parties will win a seat in the 2026 Knesset elections?
Group basis: `exact_gamma_event_id`; event ID: `996047`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 132 | new_to_snapshot | Will RZP-Zehut win a seat in the 2026 Knesset elections? [market=4424790; condition=0xbc05f2068399b5219d31f908ea45b79335f72ba6e40908126cf8fc95f88f80e5] | Yes=0.875, No=0.125 | new_to_snapshot | True | `73cb890f6dd25956733ff6dd30bd82704d6171610dc591a6d85fd1bf12594f6e` |
| context | context_unchanged | Will Ra'am win a seat in the 2026 Knesset elections? [market=4424791; condition=0x4a03c5d79804d17d0dc129778758314952c37ea4be186d6376e0f85d29415501] | Yes=0.9605, No=0.0395 |  | True | `eb414a89c33f6577d92d92a732c16255070c2d2e16efe408cbc347c5aadd248e` |
| context | context_unchanged | Will Amcha Yisrael win a seat in the 2026 Knesset elections? [market=4424792; condition=0x6b97afbd440ab5570d6a9f7851a701b4fbdc8a3f04a2d480a2945abd28b615c7] | Yes=0.25, No=0.75 |  | True | `4ba935b39e68ed3acfba9e70cc2b61144e22503dbc64e4e8712f1cca0fc2f763` |
| context | context_unchanged | Will Blue & White win a seat in the 2026 Knesset elections? [market=4424793; condition=0x074c6f1f38a7b618e9b5a6938caaf6cd78c9ec46399eb4090be76be56169b23b] | Yes=0.005, No=0.995 |  | True | `b483265a6e5807b9fe7d9fdeb8448e2a0648afed934ba6857328ef531b5d108c` |
| context | context_unchanged | Will Reservists and New Economic Party win a seat in the 2026 Knesset elections? [market=4424794; condition=0x9144a020549bc624bd925f7c6e4e0255b30f47f7f5727433287191fc4087b307] | Yes=0.47, No=0.53 |  | True | `5807203c305ebd3fb123619e9303e2330cb443a4f5590469501566a6e0fcb18b` |

### Russia x Ukraine ceasefire agreement by...?
Group basis: `exact_gamma_event_id`; event ID: `478472`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 133 | new_to_snapshot | Russia x Ukraine ceasefire agreement by August 31, 2027? [market=4338141; condition=0x2b19d23ba678929babfd5154a155eade5c957656117eb1d601ba2c2cb74f2337] | Yes=0.545, No=0.455 | new_to_snapshot | True | `e294d51e98664b5181b6dc9a3c458bfbe83a0cbda1e90177e73a90e589b45ca7` |
| 184 | new_to_snapshot | Russia x Ukraine ceasefire agreement by September 30, 2027? [market=4338139; condition=0x08f1d018dc73d4df073a64f7184ab77aff8a977c076e28383a65394668a39be9] | Yes=0.575, No=0.425 | new_to_snapshot | True | `834713d1fd80cb43b93e25285e3a1c6add05b27c0deac8dd99e4930c7f1e7ff2` |
| 192 | new_to_snapshot | Russia x Ukraine ceasefire agreement by July 31, 2027? [market=4338138; condition=0xea73edf70a088c4939d28ef861eb45db380078ac9eede411608c774ced5e944b] | Yes=0.51, No=0.49 | new_to_snapshot | True | `812fad5207ebcf6fc4e740fa5f25fb2084b1cd6ff00ba1085ebb0c45b920c862` |
| context | context_unchanged | Russia x Ukraine ceasefire agreement by October 31, 2026? [market=2243896; condition=0x6c3f1009a0c91ba9f7aae44aeadf86863b0d433b60f7a090fd00c945019aa32f] | Yes=0.022, No=0.978 |  | True | `effa73b81f6c96e9776ebbe0e3b0beb90900eede42eea1fb4658116928a693cf` |
| context | context_unchanged | Russia x Ukraine ceasefire agreement by December 31, 2026? [market=2243897; condition=0x5c19f205507ce03ff5f3be08a8090a5969ea6870cc07b902a4ca2e61dfe48fdd] | Yes=0.155, No=0.845 |  | True | `23329dc6837ebe0427dda1a11b45de927b3ea56ad3649263c3fff7cab29b8ae9` |
| context | context_unchanged | Russia x Ukraine ceasefire agreement by March 31, 2027? [market=3701687; condition=0x2ef59a55bf60ef28edad3a6eaa6ea9bcecbafa721dc9d0d1e73eb2c74516debd] | Yes=0.305, No=0.695 |  | True | `18118bc24391070004c3a260650fcee56ce395898d7037869e8f16cb887669e0` |
| context | context_unchanged | Russia x Ukraine ceasefire agreement by June 30, 2027? [market=3701688; condition=0x1e4ad3d340dbb9149ec6d2873bf6f519bddc1eb0f89665605fd90d226dd06b78] | Yes=0.48, No=0.52 |  | True | `4346178d18afe37bf26263a328c68e385e5e63adb31a90e32c34f48948070923` |
| context | context_unchanged | Russia x Ukraine ceasefire agreement by April 30, 2027? [market=4338135; condition=0xbdab12a222060b29a0238cbfff86c5108a31ee492ee67be3f292f8697eea7d31] | Yes=0.375, No=0.625 |  | True | `69173a74632c26aff4fcae476d93f03ebed54e3a3d53b8482305ca34f78ee60d` |
| context | context_unchanged | Russia x Ukraine ceasefire agreement by May 31, 2027? [market=4338136; condition=0x6160c02bc34107f6f84ad8a9f1efd42c02e607fbcc154b720949231c5558acc2] | Yes=0.455, No=0.545 |  | True | `810803aa5a207bdc3d711e0288dc33db23f7346b79e8a3381d07b6b1e2e2c6bc` |
| context | context_unchanged | Russia x Ukraine ceasefire agreement by January 31, 2027? [market=4338143; condition=0x357319ded51afc8843eb0ddcf345c2de1f7613e97357f7942e1e228961f4e723] | Yes=0.205, No=0.795 |  | True | `8ee78bbe5fa600c052792f31011234305bfaf5d1f827e818ef7ef236319b4940` |
| context | context_unchanged | Russia x Ukraine ceasefire agreement by February 28, 2027? [market=4338144; condition=0x270b8e5dac0c25d7adf5f0df5472de74c1b0ad36260a67e403120d23006ccd3f] | Yes=0.265, No=0.735 |  | True | `0e5ae957b8c517a25787bba01735b0e77b44a08567011328024a91b9d9bf46b1` |
| context | context_unchanged | Russia x Ukraine ceasefire agreement by November 30, 2026? [market=4338145; condition=0x346543618b5077cedcabb9da57cf643922dbc752a7f332fc26e0256a38bb74c7] | Yes=0.08, No=0.92 |  | True | `26b204f410404c1af2a1a6e2b00e3d3802e520557714e1b3b3963ef3f0ea7447` |

### Oscars 2027: Best Actress Nominations
Group basis: `exact_gamma_event_id`; event ID: `1188161`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 135 | new_to_snapshot | Will Virginie Efira be nominated for Best Actress at the 99th Academy Awards? [market=5685401; condition=0x1cea0c3e8394feda1090bf915ff220af27aa89aa6a3b183b66f6216b9996c602] | Yes=0.535, No=0.465 | new_to_snapshot | True | `29a0ec56ea87acc436d9b3216458826d3ba8c85253f0bf73527f5c468f6ff8bd` |
| context | context_unchanged | Will Julianne Moore be nominated for Best Actress at the 99th Academy Awards? [market=5685396; condition=0xbf26ed8be72c4f9281a2a1b562f817cf01ec5fc34948f3517e888c200c7a5c40] | Yes=0.955, No=0.045 |  | True | `8a3c1a34efb05d57ca9ed1301311e63e0e71b7b3b41d765c9bb3f83df60f4bf8` |
| context | context_unchanged | Will Rosalind Eleazar be nominated for Best Actress at the 99th Academy Awards? [market=5685403; condition=0x2f58f36b00f9bdea874591daf05bd275775107f765b3ee359588b0542405205f] | Yes=0.19, No=0.81 |  | True | `5dcc9eaf3a3fbc2a119a9fa937be551b22dbe1c55c9b31f1a5596f3a2c3361ae` |

## Batch 23 (15 markets)

### LaLiga: Teams relegated (2026-27)
Group basis: `exact_gamma_event_id`; event ID: `904908`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 136 | new_to_snapshot | Will Levante be relegated from the 2026-27 LaLiga? [market=3848380; condition=0xa9bfb777395eb2717ec18e3120558607d17a0362bb5819aaa9c146289709d09c] | Yes=0.335, No=0.665 | new_to_snapshot | True | `58ea4f28c619d5844227c601c1a6030d8a4f59bfc8f96ba21dff8929f9c21d0a` |
| context | context_unchanged | Will Elche be relegated from the 2026-27 LaLiga? [market=3848374; condition=0x61be2634a8edc562cc3d6520f9dbb4ca2f228bb4143aaae828574827ff826511] | Yes=0.36, No=0.64 |  | True | `61d7ad2e02515617b9a3e0f43ef642da236009f59f0aa92fb343ef8f10cd3f3c` |
| context | context_unchanged | Will Osasuna be relegated from the 2026-27 LaLiga? [market=3848386; condition=0xd8ee81524d5f8ecf10ac7fc4297e17372db2f0f63e8a2b904a6446ea0eef15e2] | Yes=0.205, No=0.795 |  | True | `472444e93a021cf5b90d833c377847a92f886554af58263e1bdb36ef6d455d06` |

### NJ-06 House Election Margin of Victory
Group basis: `exact_gamma_event_id`; event ID: `834363`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 139 | new_to_snapshot | Will the Democratic Party candidate win the 2026 NJ-06 House election by 25%-30%? [market=3519451; condition=0x12ed1e6a3a7a8193adc19df4469f07f228356cde75c7a2b57929f161196b46bd] | Yes=0.335, No=0.665 | new_to_snapshot | True | `fc5bbc40901a9fe4c1f37c2e220d9937393557113d479b3e60705fe270173ed0` |
| 147 | new_to_snapshot | Will the Democratic Party candidate win the 2026 NJ-06 House election by 30%-35%? [market=3519450; condition=0x2dbaf9888bcb602150200874f3e87e44b90ee6de7b444bae629557a0593168ac] | Yes=0.085, No=0.915 | new_to_snapshot | True | `f07c3c06e9b8eacdeb20ed83d86ff8a8de8486d94313351d530077d6ca37c4ae` |
| context | context_unchanged | Will the Democratic Party candidate win the 2026 NJ-06 House election by 20%-25%? [market=3519453; condition=0xc19311b097dd0c9156e4e649f22f7d99fb1e4e62be95cc8f4cf34d1cb3b39d0b] | Yes=0.3155, No=0.6845 |  | True | `b94df509b52d7cc7ddb76d57dbdb50c0f39eb0b59b24129f0dfa60f8ffeac39a` |

### Tlaxcala Governor Election Winner
Group basis: `exact_gamma_event_id`; event ID: `800725`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 141 | new_to_snapshot | Will Anabell Ávalos Zempoalteca win the 2027 Tlaxcala Governor Election? [market=3357692; condition=0x71c57eeaf5ee88e37a4a86ff04b23ac09a45d10cd8eb5bf94d585f7ef5e607c8] | Yes=0.0205, No=0.9795 | new_to_snapshot | True | `d0dedbf3cabdc6b0eebe0deed3d5ba205b11171e3c477206fe178f947cf09ac6` |

### Wyoming Senate Election Margin of Victory
Group basis: `exact_gamma_event_id`; event ID: `797333`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 142 | new_to_snapshot | Will the Republican Party candidate win the 2026 Wyoming Senate election by 30%-35%? [market=3344227; condition=0x4fb33ce35483eed63ba32ec51fa6336b7382063584d95a2c644d411a1984d5ca] | Yes=0.16, No=0.84 | new_to_snapshot | True | `b2d961d4d8e8a490a4d79a3f8ef3d8095d1389af9cac0190ec4753106e6e69b5` |
| context | context_unchanged | Will the Republican Party candidate win the 2026 Wyoming Senate election by 35%-40%? [market=3344226; condition=0xfbf0d60ef23bb9ae5ff0bd5c3240644b1a8d5c230eae6b8a449a57f79c57bbb5] | Yes=0.15, No=0.85 |  | True | `4d99ddd3cccde0298636a03f1b6703c16d109c42ff66c774f0b07d87f3f30542` |

### Third-best AI Lab end of December?
Group basis: `exact_gamma_event_id`; event ID: `1113962`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 143 | new_to_snapshot | Will Meta be the third-best AI lab at the end of December 2026? [market=5176941; condition=0xfa6ab3bdfd29bc28c7f952329bd55782f85bf3d2ca0e4fb9feb549ae43059072] | Yes=0.375, No=0.625 | new_to_snapshot | True | `710970be33115570cf76cb89cdcc9377c4d62d9762038b4b0050970cf01806b3` |

### #1 AI lab by OpenRouter market share week of October 19?
Group basis: `exact_gamma_event_id`; event ID: `1216187`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 144 | new_to_snapshot | Will Google have the highest OpenRouter market share the week of October 19? [market=5916206; condition=0x6eff72f9ccc3f72be8e65f90f4c6b5a47fe5809930c31b1b873c1faba82a3d6a] | Yes=0.0155, No=0.9845 | new_to_snapshot | True | `4f0bbc1ac5499f108982999f4e2664d5ea349cc1b66a4f0e78c8016e26cf1c45` |
| context | context_unchanged | Will DeepSeek have the highest OpenRouter market share the week of October 19? [market=5916183; condition=0xc224d8b4ce36a578c79529902352536b8080e330afac44741a6bad90f4dc15de] | Yes=0.875, No=0.125 |  | True | `e35f875775d3dad13917c5a2f6805e8db543d15bb93906f2dcf6c4937c6a2e46` |
| context | context_unchanged | Will Tencent have the highest OpenRouter market share the week of October 19? [market=5916186; condition=0xd0699efba058c0cef0f61f4becd2a97c7f4872f799cc84085c9ec433d1840e0d] | Yes=0.0285, No=0.9715 |  | True | `75f64c4143f72bdac9c261df26bac43bc98ab4a73e17c4d1c7c2c15f32967b77` |
| context | context_unchanged | Will Z.ai have the highest OpenRouter market share the week of October 19? [market=5916194; condition=0x70896bb1d994f61acf1bd188e241d12f9ed7a5f305bb13ff9d4cbfae815901bb] | Yes=0.0235, No=0.9765 |  | True | `ba9ea16397cb0392c447809bd29d1f4b17560af30241c7de3aac1db9fb27bbd1` |
| context | context_unchanged | Will xAI have the highest OpenRouter market share the week of October 19? [market=5916225; condition=0xd4148008f1925b2a58c13dc2230a7be9526e84d029da6af17511076cb2587f88] | Yes=0.005, No=0.995 |  | True | `c18206e7dc8f8a0312255939895786689afbc593033d83d0bd462335e98fe045` |

## Batch 24 (15 markets)

### Donald Trump # Truth Social posts October 20 - October 27, 2026?
Group basis: `exact_gamma_event_id`; event ID: `1203167`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 146 | new_to_snapshot | Will Donald Trump post 80-99 Truth Social posts from October 20 to October 27, 2026? [market=5794219; condition=0x9a9baf5719ec12afa8517add1dbec6f8c3592bdd5a5bcda65a840481b37aadf5] | Yes=0.052, No=0.948 | new_to_snapshot | True | `57f2ee51c1095c0da64e07b80a93691c03ebaad1bcb1e33bd0d13a1bebf33d86` |
| 196 | new_to_snapshot | Will Donald Trump post 0-19 Truth Social posts from October 20 to October 27, 2026? [market=5794187; condition=0xfa9823123243264aacb61d89391f149be624dfb834cb5244007f52d7570a9579] | Yes=0.0045, No=0.9955 | new_to_snapshot | True | `4c7728c1c6ff57c6b70e187c0fa4fcaed97ef56316b1ae063b603eb57061119b` |
| context | context_unchanged | Will Donald Trump post 60-79 Truth Social posts from October 20 to October 27, 2026? [market=5794212; condition=0x43006d5967ed104dace0c057fc56346215e889c4aa672214a02b1d2d4cd27952] | Yes=0.006, No=0.994 |  | True | `0da6a51a58a0902cf72e67862c41821deb46aa41223ade2ecf55a0a4122ad47d` |
| context | context_unchanged | Will Donald Trump post 100-119 Truth Social posts from October 20 to October 27, 2026? [market=5794228; condition=0x4befeec932c5a2957ef9bd2b39ceff963b21d9a8185420a79288a8846df652c3] | Yes=0.1, No=0.9 |  | True | `f8c5318089ba2299b6f091eaa55b89e7961063509e087dfe87a5baf23e037e1c` |
| context | context_unchanged | Will Donald Trump post 140-159 Truth Social posts from October 20 to October 27, 2026? [market=5794246; condition=0x6961382fe387bcf844975dde31bfb0da2c7f7aa0d5b7315c13082c0a5d78094c] | Yes=0.18, No=0.82 |  | True | `e67942fcbcbb7a9cbe7a474847e37e03de9f9c372499cf0c0532c6dda9fee044` |
| context | context_unchanged | Will Donald Trump post 160-179 Truth Social posts from October 20 to October 27, 2026? [market=5794255; condition=0x89361c5a0e2e11dd014555d9e69cf39dcdb2fc9a8b6f7a57ddf8969388dae7da] | Yes=0.195, No=0.805 |  | True | `bb58280d548ff6053836a31f669bb40b469527c8dd6624c9294f0c45e01354b7` |
| context | context_unchanged | Will Donald Trump post 180-199 Truth Social posts from October 20 to October 27, 2026? [market=5794263; condition=0x92b65af419791b0657e3c6d87eea4f19b0fee0952ced07f3d5e77d61e3d7fd6c] | Yes=0.09, No=0.91 |  | True | `84dda77a7c2a9ee51cea04d11e49e16e3e3660474242aa0544a34a8a6fe4f5b9` |
| context | context_unchanged | Will Donald Trump post 200+ Truth Social posts from October 20 to October 27, 2026? [market=5794272; condition=0x74932f4e3c04039d1313c9fceb4d34ef67ef87f7036be8093ae703f89256d767] | Yes=0.195, No=0.805 |  | True | `2d9260580186cbe24c713589cd9e7ed3dbf9f30f2414b2bf758509d9f0e2fc81` |

### #1 Free App in the US Apple App Store on October 23?
Group basis: `exact_gamma_event_id`; event ID: `1207589`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 150 | new_to_snapshot | Will Claude by Anthropic be #1 Free App in the US Apple App Store on October 23? [market=5837714; condition=0x0116944ebd8e51970573eab706da8c958f08bb05a64bfd08600a7f729785c90a] | Yes=0.026, No=0.974 | new_to_snapshot | True | `2c49e1ba8de4de984369656491ba5fa799e121ffe6767680cf4a2a9bbf0dae2b` |
| context | context_unchanged | Will Muse from Meta be #1 Free App in the US Apple App Store on October 23? [market=5837710; condition=0x18e696bcd7cdecbdc09da9f9c2523e46853edcdc9175dab46ae13e9a7f0b1711] | Yes=0.89, No=0.11 |  | True | `6d75a56d9aa18614a0032c892893026cd5e61821dfd8f674f99d631fd56da2b7` |
| context | context_unchanged | Will KICK - Live Streaming be #1 Free App in the US Apple App Store on October 23? [market=5837716; condition=0x3647fad3df4a3b580731a173f890a551be1c73de0f2ba2b0b303e40594e030c9] | Yes=0.012, No=0.988 |  | True | `3a28e83699804f284ee21874dcda8470bb2dbe7a2ca8bad015e8f8ae0e48ca06` |

### Georgia Senate and Governor Combo
Group basis: `exact_gamma_event_id`; event ID: `877336`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 155 | new_to_snapshot | Will Republicans win the Georgia Governor election and Democrats win the Georgia Senate election? [market=3729340; condition=0x9aa20b4b387d7038f271464dda0d3137ad72aba90827ad3ce58d18c46587aa4e] | Yes=0.49, No=0.51 | new_to_snapshot | True | `2ab19d9b122a2e771cb7f6f57c11e9c71bd80b8030f4ef3cf7676e85542179a2` |
| context | context_unchanged | Will Democrats sweep the Georgia Senate and Governor elections? [market=3729337; condition=0x975fb50d7228d0af302d55ead0f332692aecf3e7211103b3d911faae6d5b0b61] | Yes=0.52, No=0.48 |  | True | `c2aeb964f72eb713b0e9c109d5656924d0deaf3d6ef528bef4c03a8d5eafa9bb` |
| context | context_unchanged | Will Republicans sweep the Georgia Senate and Governor elections? [market=3729338; condition=0xba3301ac91a9a6024ef0dac778f6f8c3a4260396f7eaf6a11519ec4b1ab27aff] | Yes=0.019, No=0.981 |  | True | `669cf9a0683cf83c96cd6d283c086ee2ef241ac0d439b86719dd992a5c705bf3` |

### NCAA Football: CFB Playoff Top 4 Seeds
Group basis: `exact_gamma_event_id`; event ID: `801843`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 156 | new_to_snapshot | Will Texas Tech be a top 4 seed in the 2027 College Football Playoffs? [market=3362522; condition=0xf62d231c4c02ad866c468e074dfd64564fa65fcc2d265bf6f14afb56a8a70037] | Yes=0.205, No=0.795 | new_to_snapshot | True | `a25338c4f72a537ba2f9c1899e009a03e5ebf4c03f04a74d9bc40be37e9cf6c2` |

## Batch 25 (18 markets)

### NY-13 House Election Margin of Victory
Group basis: `exact_gamma_event_id`; event ID: `834398`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 157 | new_to_snapshot | Will the Democratic Party candidate win the 2026 NY-13 House election by 70%-75%? [market=3519705; condition=0xb891ed6c2535a6679dfaf50b39b75c3b2a1374a01f4a80978dc8ee53a05389c0] | Yes=0.31, No=0.69 | new_to_snapshot | True | `18e2eacfe0704f8922bc14c7d4fd65c304386e94d944764866e6fa7c307abb97` |
| 170 | new_to_snapshot | Will the Democratic Party candidate win the 2026 NY-13 House election by 85% or more? [market=3519702; condition=0xa0fcd531b082b236097396b529824e238a2b50d44df09c745c38ca036dd473fe] | Yes=0.0265, No=0.9735 | new_to_snapshot | True | `97c2897898f4d34f51601b9e7691398cc8303fd5a6252d00048395e21ccffbbc` |
| 176 | new_to_snapshot | Will the Democratic Party candidate win the 2026 NY-13 House election by 60%-65%? [market=3519707; condition=0xbbdc2a871b38085a2837b8b04fd660df428f0c4deb689461f5705e9778656216] | Yes=0.18, No=0.82 | new_to_snapshot | True | `8bb57d652a57c5430db2fb7a3f4187051c1464fdd1e448db3d25ce2bab89bfb7` |
| context | context_unchanged | Will the Democratic Party candidate win the 2026 NY-13 House election by 65%-70%? [market=3519706; condition=0x34d169271e53ccc175db0507571f85a5df91a411c7d34e9cadd44df945677d5e] | Yes=0.27, No=0.73 |  | True | `2c6dfdbdc4bf97a6efb8f4dafa5ca7bfe66ad0720d17d1f054c214acfc66664e` |
| context | context_unchanged | Will the Democratic Party candidate win the 2026 NY-13 House election by 55%-60%? [market=3519708; condition=0x976670cf89c8741a5a4953dac36683c54f7169233f8c5be9dcbf4f448252afc1] | Yes=0.0055, No=0.9945 |  | True | `fc223e25d3bd3278f3980d5cf1321d5164a76545866b0296c931cc45cc3272dc` |
| context | context_unchanged | Will the Democratic Party candidate win the 2026 NY-13 House election by 0%-45%? [market=3519710; condition=0x12bb47c2c8a032a30766490ac0b904e8b590cf642fdebf83e416dafe8036cea6] | Yes=0.0095, No=0.9905 |  | True | `8e2e5492a8d05546d12b7c909dd1cb9f618980f0070d915a47cdf193ef0767b4` |

### Which Senate races will be within 5%?
Group basis: `exact_gamma_event_id`; event ID: `769205`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 158 | new_to_snapshot | Will the Alaska 2026 Senate race be within 5%? [market=3207070; condition=0x6a14f4ebd373e9fb0c625297b8fc270f1f374916c9ace9379a3562120b5e8573] | Yes=0.63, No=0.37 | new_to_snapshot | True | `bd3577c0ea3261e107cceeffe71b9068c1ba91d4523d2b84ca41c85fd8e6b5b8` |
| context | context_unchanged | Will the Texas 2026 Senate race be within 5%? [market=3207066; condition=0x47f49915fa9852c45cbc544c6f28b7d1cf1ada1c0fd605daf9a9fd853c5084e2] | Yes=0.735, No=0.265 |  | True | `cfa4c422f80dacb9a96eec6cf614aeb512a95d808a6cfbe72a056375bd32df85` |
| context | context_unchanged | Will the Maine 2026 Senate race be within 5%? [market=3207067; condition=0xc33972d4eb2756765e308d12d96a75906880401dea62baff9a2fabcfb433878d] | Yes=0.685, No=0.315 |  | True | `9db99cc0937aef8db00fce2b948b2b71d16c5a33002fb308128cc07f62937c80` |
| context | context_unchanged | Will the Iowa 2026 Senate race be within 5%? [market=3207069; condition=0x27f1b58012548eef9670a6949563ebf920a5658ed0fc049f31e1a869432c89dd] | Yes=0.71, No=0.29 |  | True | `fdbcec8c9469352d7aa7024439ddcf4ae3d12ad6b6cb1da0064f295c76994834` |
| context | context_unchanged | Will the New Hampshire 2026 Senate race be within 5%? [market=3207072; condition=0xd891ccecfaf145c3cf1094be169387e21364defae3d6a38764455c694aa3deb5] | Yes=0.335, No=0.665 |  | True | `a9416d292887533f229d8c786a8bf214092c796a8fbb6bba429ab5e0cc5ee0b1` |
| context | context_unchanged | Will the North Carolina 2026 Senate race be within 5%? [market=3207078; condition=0xb94a183a60eb4c21568a42af274e7652e1f35563715906a92baf2ccf253a17c9] | Yes=0.205, No=0.795 |  | True | `7f04c8bc2084fb3bb29cf76f078b3f79085d3615da982d73135f69f49be44499` |
| context | context_unchanged | Will the Georgia 2026 Senate race be within 5%? [market=3207079; condition=0xc92a777e0e2ed63ed49fadb24bbdb726e968eb3e7eeb0439b0a1a1a4ac1ab493] | Yes=0.14, No=0.86 |  | True | `fa4c425b514af668f3312567a83cb418fd1713b6251eac94c362a0cf87ddb3a5` |
| context | context_unchanged | Will the South Carolina 2026 Senate race be within 5%? [market=3876144; condition=0x6d495b41a9ed33d8601f0762c20949880b56653df92d374fe31f7777d0ed2059] | Yes=0.485, No=0.515 |  | True | `34cea96835c34ed78ffa55776c387597f3ad03d8d56513e765f90e010b59e8cc` |
| context | context_unchanged | Will the Kansas 2026 Senate race be within 5%? [market=3876145; condition=0x0436e68d2a5503be0bba38f18fc0df08497b393c317039bd65b72621e5dec1cd] | Yes=0.605, No=0.395 |  | True | `eb8e3f175b3c1cd28b254c0407cf2ef0a62ef6ece6efa2e008f7c6ecbc63a160` |

### Israel Election: Yashar vote share?
Group basis: `exact_gamma_event_id`; event ID: `990635`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 160 | new_to_snapshot | Will Yashar win 18-20% of the vote in the 2026 Knesset elections? [market=4385287; condition=0x90e9062e8fb1b9735715a8087e9dcb2ab1efa926849d87dcebc51989bdb082a9] | Yes=0.285, No=0.715 | new_to_snapshot | True | `cfa80b3c756af8096512bfadf98d3ea3a9c67e585672818d90ecaa1bab585520` |
| context | context_unchanged | Will Yashar win 20-22% of the vote in the 2026 Knesset elections? [market=4385289; condition=0xacd04079c8ad93bf55c25a6297de45aa5564f60fe5ba82418a11f67cd8780af2] | Yes=0.123, No=0.877 |  | True | `66c620a236cedce222c454fc579dac04a3b911e1dbb1a01084370d9f33cf3bed` |
| context | context_unchanged | Will Yashar win 22-24% of the vote in the 2026 Knesset elections? [market=4385291; condition=0x1c34780d7e9f7fc4f971f80b1c350e4a2d0112f1be01801601442106c65c5fba] | Yes=0.0115, No=0.9885 |  | True | `3078791f84715f9067fd119f3d8e0803c37ca786123523f182559baeb473b824` |

## Batch 26 (20 markets)

### October Inflation US - Annual
Group basis: `exact_gamma_event_id`; event ID: `1189074`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 161 | new_to_snapshot | Will annual inflation be 3.8% in October? [market=5691089; condition=0x2f490d6f6f72c535e24fee8881a26b394c362270d2080f1e7f0adf2ffd5f4c8c] | Yes=0.0475, No=0.9525 | new_to_snapshot | True | `efbf35a8a707d9b1e03a9b0d4dcd8d262042644224a127d9e6b22c49940f3112` |
| context | context_unchanged | Will annual inflation be 3.7% in October? [market=5691088; condition=0xf464b826a86e0db857ae3db6362b91b4d2c289d5b14f7065b2d76fa89e44f3bd] | Yes=0.82, No=0.18 |  | True | `452d4219f67d68b605d568631dba9f49d05721f3f2974ee522da02e97dd8a50c` |
| context | context_unchanged | Will annual inflation be 3.9% in October? [market=5691090; condition=0x0663378212ab1da5727f4c5eb768f0334e0eb141be456c1dc4816063101645a4] | Yes=0.019, No=0.981 |  | True | `924be13a521a61ce4133226cda05340ffa9e997c06dc59c88916cfba3ee0927b` |
| context | context_unchanged | Will annual inflation be 4.0% in October? [market=5691091; condition=0xd5e110fb1375365e1083bc118e3a3b8695edfc740f582f040b51e34aeba29771] | Yes=0.0215, No=0.9785 |  | True | `ab3dca4906c37e1c4420a0f09f07370030815d225f6d4d6fd670aeb601e3cb16` |
| context | context_unchanged | Will annual inflation be 4.1% in October? [market=5691092; condition=0x5abcad5f01d7c41bbd1af2fa678423cb0a15c17c009c2ee418df44bb3e199e43] | Yes=0.0075, No=0.9925 |  | True | `98c3e5f9cddf5abbf7e3ecffa8190870d587c4c5cf65eb4b4246f99a447cb438` |

### Which characters will appear in Avengers: Doomsday?
Group basis: `exact_gamma_event_id`; event ID: `333162`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 162 | new_to_snapshot | Xochitl Gomez as America Chavez? [market=1818693; condition=0x193811133067252c62713ace40b7e839ee92deb66e6c6de6650771e495ee4eeb] | Yes=0.52, No=0.48 | new_to_snapshot | True | `4640a34a24f64284078f03ff02780ff8f63f51f219a6c7347bd467578c18d385` |
| context | context_unchanged | Iman Vellani as Ms. Marvel? [market=1818694; condition=0xaa171f20edcf257588ea814e41dd1a17030db545de05ee27be30beaddbcb3296] | Yes=0.785, No=0.215 |  | True | `38f503e39d76388093aa2d8024cd856efc7d6684f8ef71720952bebfa32746fe` |
| context | context_unchanged | Mark Ruffalo as Hulk? [market=1818700; condition=0xd6696b1f8f76b02c28b1ad2288da9080cdb5f12a90fc6330cd1f4bd06a2ddd35] | Yes=0.695, No=0.305 |  | True | `5326f8cf54c22e14f2c94eab2b3a951b9edf140a67209db52ef2dc9a94eff786` |
| context | context_unchanged | Tom Holland as Spider-Man? [market=1818702; condition=0x116ef6172ae1fa2b206be1910f41a27f4a25bb7ed54d761157973a59518bd3ad] | Yes=0.41, No=0.59 |  | True | `0b99c2f8e572b96a420671f411462b3612c8e6fa6573ae6fdafc65690e174d5c` |
| context | context_unchanged | Don Cheadle as James Rhodes / War Machine? [market=1818703; condition=0x6fe9f26e476b3db70ddda41e130dae8afe499cb78ef247daaf3336217366ebde] | Yes=0.32, No=0.68 |  | True | `deb44de36d2760624a052af08fd7053d10f672f25f9bf3073c2959f469733847` |
| context | context_unchanged | Gwyneth Paltrow as Pepper Potts? [market=1818704; condition=0xfb0b73b8b75b7a5b16c8ef33527db8419eff97e0f886cbd16a8a2d22af350178] | Yes=0.615, No=0.385 |  | True | `087a5f7410dee2d42819354fabf9831827987ce554b3402febfadede0f06390a` |
| context | context_unchanged | Jon Favreau as Happy Hogan? [market=1818708; condition=0x76415d8735b0e5bf13d2ec0473ead9bd40f07ea8c82487328408db95cb3a602f] | Yes=0.51, No=0.49 |  | True | `de95a16656b749eb4596cba505ac7b11972a48c18d4b6e651a535723ccdf9ba0` |

### NY-16 House Election Margin of Victory
Group basis: `exact_gamma_event_id`; event ID: `834395`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 163 | new_to_snapshot | Will the Democratic Party candidate win the 2026 NY-16 House election by 55%-60%? [market=3519664; condition=0x2270d700b658a8502c7ca7c483e57ec63b2115b7aa345c5e1a81b37a39d354c6] | Yes=0.1365, No=0.8635 | new_to_snapshot | True | `e78b9c3229520168352afca251eaba5011d4c7cf38df23d5ba85dd249715fc38` |
| context | context_unchanged | Will the Democratic Party candidate win the 2026 NY-16 House election by 60% or more? [market=3519663; condition=0xe8565f599c314468e55aa56a580ef2f0ecf08d23fd6e6c7e3c389c32a00e069b] | Yes=0.06, No=0.94 |  | True | `280c032d25d0ed678fae9730229af49307fad9210157f802aa27d44a891ef4fe` |
| context | context_unchanged | Will the Democratic Party candidate win the 2026 NY-16 House election by 50%-55%? [market=3519665; condition=0x617e2b72d088566f5aaaba46558bc64bef292381faa9da850078c852f804160a] | Yes=0.27, No=0.73 |  | True | `513bbda3b40609c8eb514e4b5bd935ab8582d5717a301528179069a9c31196f0` |

### UEFA Champions League: Team to Finish 9th-24th in League Phase
Group basis: `exact_gamma_event_id`; event ID: `1024892`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 164 | new_to_snapshot | Will Club Brugge finish 9th-24th in UCL league phase? [market=4566440; condition=0x0ec7b173a837785ffa271b84bb36d3a84512d44d55e1c0847f370b1b61878ece] | Yes=0.525, No=0.475 | new_to_snapshot | True | `5f7d157e3dc97f5142019489ac32462a0d9fe274f3cdc5c3f794300227d11d27` |
| context | context_unchanged | Will Arsenal finish 9th-24th in UCL league phase? [market=4566368; condition=0xbcd4e186df87489020a706df5a93b60d3d9c7f2058f4202395f955b70d93f049] | Yes=0.115, No=0.885 |  | True | `b75a8c3bf7c35f2c25a5dd887731925fc7f342702a83415e451f83e3c8d1b70d` |
| context | context_unchanged | Will Bodø/Glimt finish 9th-24th in UCL league phase? [market=4566460; condition=0xd0fb03e4f839ee98dc4ec11cb1412aa2f1f22afee50e28b96b5f88bc8ed9214f] | Yes=0.495, No=0.505 |  | True | `fd0d6c8a951d93d2ea465d466a0ee3417b8e0e0d044d2587d02cad802826ee29` |
| context | context_unchanged | Will Slovan Bratislava finish 9th-24th in UCL league phase? [market=4566463; condition=0x2e4857c0e3f6c828324cf18ba65565b222e28139e43af87812edc007b6cdae49] | Yes=0.11, No=0.89 |  | True | `ca1bc5f9c4191ea099df4e6f7a57ffdd9815867e275df21fae93eb2faa5e3104` |

### Core CPI YoY - October 2026
Group basis: `exact_gamma_event_id`; event ID: `1189689`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 166 | new_to_snapshot | Will Core CPI YoY be 2.5% in October? [market=5699279; condition=0xe8e06f4aba9be07fb3fbf4f156640643ede369b8e0964aaa0f3d6426dc6c8a93] | Yes=0.13, No=0.87 | new_to_snapshot | True | `a94c59b9b850f5357ca0471fe85ed8239370b6d90154dc632370be6557d13fd4` |

## Batch 27 (16 markets)

### Oscars 2027: Best Documentary Feature Film Winner
Group basis: `exact_gamma_event_id`; event ID: `805189`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 167 | new_to_snapshot | Will Nuisance Bear win Best Documentary Feature Film at the 99th Academy Awards? [market=3377269; condition=0x9ae1925c911c493a95587d1caef2591af3caa7a6608bfb85204946be47e31c1f] | Yes=0.035, No=0.965 | new_to_snapshot | True | `e852296f1a9fc11e117270b1f196acd2e96ec954abc4fa7977f0f6b4c186c9f9` |
| context | context_unchanged | Will "NAZA" win Best Documentary Feature Film at the 99th Academy Awards? [market=3377275; condition=0x653a7f2a51c3806c0261c72d4dae8e65ad67e488df2373501bf7c9113e014b37] | Yes=0.21, No=0.79 |  | True | `455ac4b7047f615996eb36419ae36c6357de4a8bc0334c5a800a31e57bb2a1ce` |

### Abha Saudi Club vs. Al Kholood Saudi Club
Group basis: `exact_gamma_event_id`; event ID: `1138931`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 168 | new_to_snapshot | Will Abha Saudi Club vs. Al Kholood Saudi Club end in a draw? [market=5339866; condition=0x27a25290f5a2e2ff16c95da4e5c6226b4a5065dfb9dc71d208bfc9194a120f81] | Yes=0.275, No=0.725 | new_to_snapshot | True | `c3784ad845bf62bfa7624e8b5d12234e4235012c799bc01be27bc17ebca12ee2` |
| 251 | changed | Will Abha Saudi Club win on 2026-10-19? [market=5339865; condition=0x8ac7a6f0233efa90560ea129198c8110f34441da206676b227e6c4049e58dd0a] | Yes=0.3, No=0.7 | best_bid | True | `04eca8ae30ce3b7763b2dfde94127f0cb68b97d5e2953bd60e1315b01f94f456` |

### How many dissent at the January Fed meeting?
Group basis: `exact_gamma_event_id`; event ID: `778684`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 173 | new_to_snapshot | Will four or more people dissent the January Fed decision? [market=3247716; condition=0xf277e4ba45a99eb3c6dd9ccc8aca8d34a44cc01c76d83af597c77c3bb021ca52] | Yes=0.025, No=0.975 | new_to_snapshot | True | `9b1c6c5b6f3d81e54f1a7fafe1148632d704f2239005e21bc7734f0407ce1517` |

### Vermont Governor Election: Turnout
Group basis: `exact_gamma_event_id`; event ID: `870918`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 174 | new_to_snapshot | Will total votes cast in the 2026 midterm election for Governor of Vermont be between 225,000 and 250,000? [market=3697774; condition=0x55f426365adb8c0b2e680c1f5c96df403d7872ae3dd1f89fe236d7486020b5f6] | Yes=0.048, No=0.952 | new_to_snapshot | True | `a790e7a83f0899ce63cb73b274aad6e9dd0161ada7ba9ad3ce8d12addeeb57c0` |
| context | context_unchanged | Will total votes cast in the 2026 midterm election for Governor of Vermont be between 275,000 and 300,000? [market=3697776; condition=0x2ea9ed6231918b22f056f77f5a43148c1e1b48ad439bb2f5b39f0d5c688cdc2b] | Yes=0.35, No=0.65 |  | True | `430fdeb21bad2b335f39c5c01a4dc8794c90624449d39eb56842112bdc16e737` |
| context | context_unchanged | Will total votes cast in the 2026 midterm election for Governor of Vermont be between 300,000 and 325,000? [market=3697777; condition=0xe06486ce91164cd3f310c384b13ab35c8c6b8de24c13dbe47e8588ac432479d2] | Yes=0.31, No=0.69 |  | True | `01a170240a023cf530f2c460c8fbffa39226cd2a3bd4e21b10fc5c729a7c1d2b` |

### Billboard Hot 100 #2 Song Week of October 31
Group basis: `exact_gamma_event_id`; event ID: `1207509`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 179 | new_to_snapshot | Will "expectations - Olivia Rodrigo & Chappell Roan" be the Billboard Hot 100 #2 song for the week of October 31? [market=5837112; condition=0x4c5b56c778e7c75c90e6b07bf212da7a26c6b16968c16fbba0a3003886d6cd22] | Yes=0.0285, No=0.9715 | new_to_snapshot | True | `816c29ede189ed79ef8c147bfdb304e21c711be7158370759c9acbbfc88b8e6e` |
| context | context_unchanged | Will "Patient Zero - Taylor Swift" be the Billboard Hot 100 #2 song for the week of October 31? [market=5837106; condition=0x006f164ec54592d4ad6c1dfa3ed183a65584bcb2762decfd93e4ae0decbdaaa0] | Yes=0.14, No=0.86 |  | True | `afceeb047a3fd951f02ce5334023a967549911e7f07250e8a9479c1634129b99` |
| context | context_unchanged | Will "Housewife - Tate McRae" be the Billboard Hot 100 #2 song for the week of October 31? [market=5837111; condition=0x557f39f1e6ce61ed34e803e48629a59183c5e00d1cc580f3acbc617edb3949b0] | Yes=0.36, No=0.64 |  | True | `87c57a9ad19af05b93ae73508d3fb61d40e1b9cb07fff76897add53dde92002b` |

### AP calls the House by...?
Group basis: `exact_gamma_event_id`; event ID: `1182996`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 180 | new_to_snapshot | Will AP call US House control by November 30, 11:59 PM? [market=5649617; condition=0x044bad04a9fde3a920b887ad423ad60bb7a1572988c102f2750c9ad4808c96fd] | Yes=0.9465, No=0.0535 | new_to_snapshot | True | `af7db002ac04e77056e59b3b06a55891271becbaf0eecbd336267f0284641a15` |
| context | context_unchanged | Will AP call US House control by November 5, 11:59 PM? [market=5649614; condition=0xf81ca3dd6a1fd0844575b079750f51c77766b5ba8bdcc4267327423da54e322d] | Yes=0.901, No=0.099 |  | True | `ea535dcad466e07dac0e1db0988ef5e7a447b58b9ec9d934bb9e700f7342fcc3` |
| context | context_unchanged | Will AP call US House control by November 6, 11:59 PM? [market=5649615; condition=0xcb97e18f23708d605300d22ad1c9dc2e32d864f60e61fb68cf060fe03909d7cd] | Yes=0.969, No=0.031 |  | True | `8ede2d0bebd8b92f99da580c835d4be5f7ed4ffb7911a820634e5e12ef088d31` |

### Oscars 2027: Best Original Song Nominations
Group basis: `exact_gamma_event_id`; event ID: `1198846`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 181 | new_to_snapshot | Will "La Nieve" from The Black Ball be nominated for Best Original Song at the 99th Academy Awards? [market=5770392; condition=0x6735b6e9c6261b5c3173d0a2a71db679f1d2490ef418a964a28a3661005ca2ca] | Yes=0.895, No=0.105 | new_to_snapshot | True | `83d562207c92e1ed474deb2cf5f2329c3c56da7dc80273f3ae3952ee88747273` |
| context | context_unchanged | Will "This City May Have Chewed Me Up (But It Hasn't Spit Me Out)" from The Debut be nominated for Best Original Song at the 99th Academy Awards? [market=5770395; condition=0x2123ae856c85bbd4ce175948b118721e74fbbed95fa3218833b0bec8d6e6bdd1] | Yes=0.71, No=0.29 |  | True | `6e46d75c46dcc23981390beef3225c538ab824e6b7db899f858d23e25604c103` |

## Batch 28 (18 markets)

### Serie A: 2027 Champion
Group basis: `exact_gamma_event_id`; event ID: `659488`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 183 | new_to_snapshot | Will Juventus win the 2026-27 Serie A Championship? [market=2771200; condition=0x4481fa628d6e78cabc77c609d125fe67bb8aaf2c95f8ce20039670d68632dc65] | Yes=0.05, No=0.95 | new_to_snapshot | True | `36985b35da0bf9dd894d915e4b10cd063e3dd835679612d374740a9f92a84b36` |
| context | context_unchanged | Will Como win the 2026-27 Serie A Championship? [market=2771196; condition=0x697c7b5b929ee29bb9a88b74f3d13f9f41cd83c9e6116ad2ed3fdc5d2ec2c7d1] | Yes=0.044, No=0.956 |  | True | `20622d9358ca7be255b0b45710864194ee76f90351eef17149118c7312b68d53` |
| context | context_unchanged | Will Inter Milan win the 2026-27 Serie A Championship? [market=2771199; condition=0xfce63f3ddcc6fb3409de3ac48ec4e1c457f0cacac51017a349ab7f219496042e] | Yes=0.615, No=0.385 |  | True | `84b7ce0401a63a8726f4af017cf09e8c0dc5b7c13b92510decc0949bcdfae873` |
| context | context_unchanged | Will Lazio win the 2026-27 Serie A Championship? [market=2771201; condition=0x8c4f23fc4e00d0a656a02c8fa808364b928a2ae27eb9cbe07d962d57d902c800] | Yes=0.035, No=0.965 |  | True | `56419323b7f735511ec709537876fb55b72e1285b700676d2b03af18d850d657` |
| context | context_unchanged | Will Roma win the 2026-27 Serie A Championship? [market=2771206; condition=0x9997d2727860b21d4c7ddaccf6606c3dd8fba70e9c0ff08b00e929eaa082fdb7] | Yes=0.1575, No=0.8425 |  | True | `974b73bdc597bbfd1bc139e95d4f11b82de860aff26ff85db3d4ee2e68d7bba9` |

### TX-22 House Election Margin of Victory
Group basis: `exact_gamma_event_id`; event ID: `834891`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 186 | new_to_snapshot | Will the Democratic Party candidate win the 2026 TX-22 House election? [market=3523917; condition=0xeed530444d9e6f272e6e9933417ef189f0bc0a0bd1bab3e0a988fa7758ccfbf9] | Yes=0.041, No=0.959 | new_to_snapshot | True | `4532f79d521b1e88c016981590bb87979ec34c2b0f9b0bb8b1bf590f75497895` |
| context | context_unchanged | Will the Republican Party candidate win the 2026 TX-22 House election by 30%-35%? [market=3523910; condition=0x9c170bdafb74595e1e36a6aead1a7907ce2dc29fa3f1d141fdc79777f57f16f2] | Yes=0.0425, No=0.9575 |  | True | `cfa7ca2d391d1b664e74f7431e1dc4778ee8ca6d0ea41a5ea144af03ee591e68` |
| context | context_unchanged | Will the Republican Party candidate win the 2026 TX-22 House election by 15%-20%? [market=3523913; condition=0x158b1de8d964aa7f3d0d0a4ccc1529b8f4f9266da50ac24e04e0491ee799b716] | Yes=0.295, No=0.705 |  | True | `68921bdcc2a207d224dacddc71639777bf2203e7b5366bc6af556e290a02ea91` |
| context | context_unchanged | Will the Republican Party candidate win the 2026 TX-22 House election by 10%-15%? [market=3523914; condition=0x6b0c6e3073c0a4a92ce26f80cfd4851fd70d7fb8435a438e8e5aead9ff3d9107] | Yes=0.325, No=0.675 |  | True | `21db3f5208c5f1096f2b4c1beedefb894679ced1e41291e89e667be6a83bdc38` |
| context | context_unchanged | Will the Republican Party candidate win the 2026 TX-22 House election by 5%-10%? [market=3523915; condition=0x8c59c65c740cdb0b79861449922b9231b2c991833ab6f6957a521c60754e8d5c] | Yes=0.205, No=0.795 |  | True | `a381ce35fbcad3067b77c4ed621a64878c14989de12ed09e18ced232b18deb73` |

### IL-08 House Election Margin of Victory
Group basis: `exact_gamma_event_id`; event ID: `828088`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 187 | new_to_snapshot | Will the Democratic Party candidate win the 2026 IL-08 House election by 15%-20%? [market=3488502; condition=0xe43a4a68150b713a0913b7bde7b15800fe0f99b662e1ece8303ae27c3de14a60] | Yes=0.165, No=0.835 | new_to_snapshot | True | `e7061e35c46f3552e74d039ba97efaab1a2e3c9e822a6a604808b7e92c4052ae` |
| context | context_unchanged | Will the Democratic Party candidate win the 2026 IL-08 House election by 25%-30%? [market=3488500; condition=0x2270e7b95d3f7655a6314d09d5004f0b8e1d44751349d489cc293bb5555365c1] | Yes=0.275, No=0.725 |  | True | `f795321acc8e237547fea1752e576900ebcc19eeeba1b5976657ea6cad9e7f38` |
| context | context_unchanged | Will the Democratic Party candidate win the 2026 IL-08 House election by 20%-25%? [market=3488501; condition=0x041265c1746b0e801835de4e7186f97ba8a17bfd82f2634278986757fc71e9a8] | Yes=0.345, No=0.655 |  | True | `b4bae478b5e06ad91e5d5c77be4933f9b3ab98dd1dcccf392e89afe7ec5a742b` |

### Oscars 2027: Best Director Nominations
Group basis: `exact_gamma_event_id`; event ID: `1198837`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 189 | new_to_snapshot | Will David Fincher be nominated for Best Director at the 99th Academy Awards? [market=5770364; condition=0xccdf3f166afd02c076a7c5ce017a22225024346139e2599f818912c69bd107ee] | Yes=0.14, No=0.86 | new_to_snapshot | True | `483ea4083676b080eaf6ef7c90cf924861835c42a59ea78bf1ea6fce81e6bd21` |
| context | context_unchanged | Will Javier Calvo be nominated for Best Director at the 99th Academy Awards? [market=5770356; condition=0xb0b818d5fe586b6c05c46b1f5de8d2d7c2ce77a750e15412d9811707f1d7c5ee] | Yes=0.85, No=0.15 |  | True | `69c1ea890f02aa856921ca575d868796cd314fa2d8c3bb0501ac5457cfce86bd` |
| context | context_unchanged | Will Olivia Wilde be nominated for Best Director at the 99th Academy Awards? [market=5770359; condition=0xc1a641c54d946c6b45e4e43c6d072108aa71e8b087c83697c9f457775d0c6e62] | Yes=0.5, No=0.5 |  | True | `f1222b803d161408422831010cd6f3da0d5ffc62eb99a4143dc7a30e3cf61b79` |

### Oscars 2027: Best Live Action Short Film Nominations
Group basis: `exact_gamma_event_id`; event ID: `1193417`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 190 | new_to_snapshot | Will "Spilled Milk" be nominated for Best Live Action Short Film at the 99th Academy Awards? [market=5726217; condition=0xd7bd1acd0d79edb2515046c620af063c1f5f0e247600673173bbf3b4d1a6ff98] | Yes=0.305, No=0.695 | new_to_snapshot | True | `a331c5b810672d7991ea516932d0dc800a350b1949d712aacf9116a997673874` |
| context | context_unchanged | Will "32B" be nominated for Best Live Action Short Film at the 99th Academy Awards? [market=5726207; condition=0xbe0c0a66f5f2ff3a432f6d87793b6846572ba4c9aabcb71780ddf4ccc11a8f1c] | Yes=0.145, No=0.855 |  | True | `ecf1edc4a12706f650b85dd0397ad31058a05cda100df73c35048940101b077b` |

## Batch 29 (19 markets)

### MLB Postseason: World Series MVP
Group basis: `exact_gamma_event_id`; event ID: `1105184`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 191 | new_to_snapshot | Will Drew Rasmussen win the 2026 World Series MVP? [market=5139858; condition=0xd2debbcf803aae3fa2f05e1263728fdc6f4acd0a8efa622bd5ce7a95d75929b3] | Yes=0.033, No=0.967 | new_to_snapshot | True | `d76ee36e9d04fbfc95073db33a464a0685327d51ebf2d3a59c993cbcb9d43de7` |
| context | context_unchanged | Will Yandy Díaz win the 2026 World Series MVP? [market=5139862; condition=0xc2357f8f5adefb7730e8ecd05fc1df1ea3b93d88aeeb67101eca5067919b8bf3] | Yes=0.072, No=0.928 |  | True | `a0d4aeaaedad382b60fb3beb7b64c7ed4ab0f8bcc3d64be5eb107d507590b929` |
| context | context_unchanged | Will Brice Turang win the 2026 World Series MVP? [market=5139897; condition=0xfccc58c1712def42ee3dc677471221404f321db6ce3df8b095189fb3339925fc] | Yes=0.081, No=0.919 |  | True | `7bdda69ac05121111d7caee6045c3fe0dcd295cf8ed018ecb1dd7533d6a9c644` |
| context | context_unchanged | Will Jackson Chourio win the 2026 World Series MVP? [market=5139899; condition=0xb4d72e71dc0527ae9e9fecbf8d388b084c0eb9dbda01304068c164038133550f] | Yes=0.159, No=0.841 |  | True | `ee6d951b451e0fd4476600af87c5b1b9a0369f2d3827ce0aa930a189b1d2bb1f` |
| context | context_unchanged | Will William Contreras win the 2026 World Series MVP? [market=5139903; condition=0x14ea913cca03f3119522d7cebe9c15d402949ab653385c48309f66ae24ff65fe] | Yes=0.1135, No=0.8865 |  | True | `e8aa67b1deb920d8053c9fd1cbffab0ebcd91e70d23e10963ab7f3cdee49caeb` |

### NCAA Football 2026 Mountain West Conference: Winner
Group basis: `exact_gamma_event_id`; event ID: `779025`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 193 | new_to_snapshot | Will North Dakota State Bison Win the 2026 Mountain West Championship? [market=3249919; condition=0x6fa0b8c1dfadcc2b0f6fd24486e361afb115c2f4934bf7dcb02075b682cd5f66] | Yes=0.28, No=0.72 | new_to_snapshot | True | `2ce05f93925befed3f046348eca9562372bf4f2b6e7006c65c4b71769efca647` |
| context | context_unchanged | Will New Mexico Lobos Win the 2026 Mountain West Championship? [market=3249918; condition=0x1946874936c419017969fb0495a36adf3a0385824177a791a976c11535a8036f] | Yes=0.515, No=0.485 |  | True | `567de163ad4efdfcdb38bfa3d83617df836e721faed1dbc82560132360454528` |

### Oklahoma Senate Election Margin of Victory
Group basis: `exact_gamma_event_id`; event ID: `797307`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 195 | new_to_snapshot | Will the Republican Party candidate win the 2026 Oklahoma Senate election by 0%-10%? [market=3344072; condition=0xf71f81a54f84d01305d42237146d9483608fd7ef271b1dce9de8c75908618501] | Yes=0.0575, No=0.9425 | new_to_snapshot | True | `86b24d67af8779e13048e6e0e511408dd6a07c19adbd9acea0726cfeedb8b3a5` |
| 247 | changed | Will the Republican Party candidate win the 2026 Oklahoma Senate election by 25%-30%? [market=3344068; condition=0x5c23fbceaea786a7854cd298eab3c30d03d9958d606488bb945f66d3adb98e13] | Yes=0.215, No=0.785 | best_ask, spread | True | `58b37e2cdc4cd878ec6ebd5670c0afcce370f33621fd132a26f44fa89690043f` |
| context | context_unchanged | Will the Republican Party candidate win the 2026 Oklahoma Senate election by 45% or more? [market=3344064; condition=0xafe96eb461b90eee8320b77130cc9362790531b3aad01ba1503577892be33c62] | Yes=0.02, No=0.98 |  | True | `f6fbf8c8433319ab32d655cc0ccac8f09ae91824a1b92feaf6344cd47a036571` |
| context | context_unchanged | Will the Republican Party candidate win the 2026 Oklahoma Senate election by 40%-45%? [market=3344065; condition=0x55a883c416c36f46ab597ba5e1d3adad886a2f26d48ec728c11aa2fd59de54fb] | Yes=0.019, No=0.981 |  | True | `4842759c4d7bda62d6b9eb3d5433034307f7a74299a1c60614903360f5262cd2` |
| context | context_unchanged | Will the Republican Party candidate win the 2026 Oklahoma Senate election by 35%-40%? [market=3344066; condition=0xf9c23a31347a768fcf831fd00c2a3567b39bf7c087f60ce630766182b2563536] | Yes=0.085, No=0.915 |  | True | `35bf0886394106865e4540928ccdc6f983967d3b8216c850ae346e61724505ee` |
| context | context_unchanged | Will the Republican Party candidate win the 2026 Oklahoma Senate election by 30%-35%? [market=3344067; condition=0x1160e3f6612f030331bac94f2e59dcc3ec5cd1f66ba444031f587d63e8fc9937] | Yes=0.115, No=0.885 |  | True | `c79653525875501530b722d43a4b388278a15639c74abd8c7c2096d59a903596` |
| context | context_unchanged | Will the Republican Party candidate win the 2026 Oklahoma Senate election by 20%-25%? [market=3344069; condition=0x48920cc0fc407e5ac57419ebc578a80c14ed97b1ebdc0717164f8ad08d846792] | Yes=0.22, No=0.78 |  | True | `808450cbd63317f9c661d4e6885bfb67f6c9c2fe96c62d1ca85881b9b44ab938` |
| context | context_unchanged | Will the Republican Party candidate win the 2026 Oklahoma Senate election by 15%-20%? [market=3344070; condition=0xb0d635716e64e0f0f8c7c762a03bf4693077b8787520f1692474e17d7d47c3b1] | Yes=0.15, No=0.85 |  | True | `6837ce7ed3827084882c45ab736dc583da2c2533cb9c32df09d865eb3e64557b` |
| context | context_unchanged | Will the Democratic Party candidate win the 2026 Oklahoma Senate election? [market=3344073; condition=0xf3f0b72083c971f268d1b551595cdb8ea299d4dbd704a87371937cc5094596c7] | Yes=0.0195, No=0.9805 |  | True | `786a3881b86c5fc367ac317b540a51749c70bdee4839a1d0013f6f47d7d44f5e` |

### Oscars 2027: Best Documentary Feature Film Nominations
Group basis: `exact_gamma_event_id`; event ID: `1188317`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 197 | new_to_snapshot | Will "NAZA" be nominated for Best Documentary Feature Film at the 99th Academy Awards? [market=5686330; condition=0xdc8045b1226991799747eebcaccf96153cc055b3c24e71991d2eb6a2d3994ed6] | Yes=0.87, No=0.13 | new_to_snapshot | True | `f0bdd8912ed3cab16c0c5d76b3e1945cb362ae09540496f224b4c260892c4f7e` |
| 239 | changed | Will "American Doctor" be nominated for Best Documentary Feature Film at the 99th Academy Awards? [market=5686334; condition=0xab48071f428e46701a3c385f0a9095664eaa7752a96c32fb8ff61bcca7b3f198] | Yes=0.55, No=0.45 | spread | True | `fca77753cd88b3a19fd372e81c70f82f9f8f4d93d62e0a5a091252c410019837` |
| context | context_unchanged | Will "Nuisance Bear" be nominated for Best Documentary Feature Film at the 99th Academy Awards? [market=5686336; condition=0x95028724843ed8a40b5402e82d3cff73db9df306a98941bca22c4850c06f28f0] | Yes=0.18, No=0.82 |  | True | `d22964a90b1c7aa81224a22b5817d924bfb9e2b22d1f418218c843d27cbcb982` |

## Batch 30 (20 markets)

### Bank of Canada Decision in October?
Group basis: `exact_gamma_event_id`; event ID: `708477`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 198 | changed | Will the Bank of Canada increase the target for the overnight rate by 25 bps at the October interest rate announcement? [market=2941849; condition=0x13f5c06545b93357de46e704a3f0ca309e9e1506d7f120b1f326237d5ea65f3c] | Yes=0.5265, No=0.4735 | best_ask, best_bid, no_price, spread, yes_price, outcome_prices | True | `d381a7f1af1ac71fc394c906f7bfa29de64761f7e9963e555b60be527a038fbe` |
| 199 | changed | Will the Bank of Canada make no change to the target for the overnight rate at the October interest rate announcement? [market=2941850; condition=0xcb7a1f14ecafc99a69ebc7914929d7ca8b395194f8d8b45ef23f33610f811218] | Yes=0.48, No=0.52 | best_ask, best_bid, no_price, spread, yes_price, outcome_prices | True | `dd6e0d6cc4574f34f899df7c09cfd677d61076d8c918887e239a5d06aef739b2` |

### Bank of Canada Decision in December?
Group basis: `exact_gamma_event_id`; event ID: `991303`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 200 | changed | Will the Bank of Canada increase the target for the overnight rate by 25 bps at the December interest rate announcement? [market=4393418; condition=0x033013a4a579b40f3407b3114bab8fe0f8ffe8a3a0a78c83c3d00e7524ce1589] | Yes=0.4, No=0.6 | best_ask, best_bid, no_price, spread, yes_price, outcome_prices | True | `2e23ca145ecf8f4f06487ff008ae993b370933579cad7a00c55c0bf10d0130d4` |
| 211 | changed | Will the Bank of Canada make no change to the target for the overnight rate at the December interest rate announcement? [market=4393420; condition=0x7044a9f0a1d98f566283b205b72b6bd6728ba5adb712f30e071462e5d0552568] | Yes=0.585, No=0.415 | best_ask, best_bid, no_price, yes_price, outcome_prices | True | `a727d2a59678f9eebbe6cbb884dcbee7c534bcafcf2872862242c5ae2adc5ff0` |
| context | context_unchanged | Will the Bank of Canada increase the target for the overnight rate by 50+ bps at the December interest rate announcement? [market=4393415; condition=0x09a38604fd30d880eff96941697e0540dc7e94f92b4f05b4d911bcdd034f2484] | Yes=0.01, No=0.99 |  | True | `7f17c05bff5bce3fe26e18f6d5fd950cebb17dcc97f3c02c5a87a33bbbf26489` |
| context | context_unchanged | Will the Bank of Canada decrease the target for the overnight rate by 50+ bps at the December interest rate announcement? [market=4393425; condition=0x242e092e6ec264f73009ebc1c54feb6dc5095a8642ae9591093c26ced0e2ad78] | Yes=0.0095, No=0.9905 |  | True | `0c5922fc20a68f73d98d1fa1900fd911c0696cba86bd55e8af4af02a6830a65c` |

### What will the peak RONI be for the 2026–27 El Niño?
Group basis: `exact_gamma_event_id`; event ID: `867162`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 203 | changed | Will the peak RONI for the 2026–27 El Niño be 2.5 or above? [market=3680999; condition=0xbbd3a0e2bf9512aca0676b07657e6056a1a7d90efc0d03cff8ad4e84562b4d4d] | Yes=0.745, No=0.255 | best_ask, best_bid, no_price, yes_price, outcome_prices | True | `cf8be6e7aabea17bcc8783f8ce7ccd424dfd5f898353898d6d64504ffc509651` |
| 212 | changed | Will the peak RONI for the 2026–27 El Niño be at least 2.25 but below 2.5? [market=3680998; condition=0x3a311da04811ff7c8e003f14cd0ea80a7b95b51812b604228866874e3cd002bd] | Yes=0.245, No=0.755 | best_ask, best_bid, no_price, yes_price, outcome_prices | True | `19dc0d5fd246c3432d3416195e40feb5c50a032ee28aafd30e69998a2db52d68` |

### What will Natural Gas (NG) hit Week of October 19 2026?
Group basis: `exact_gamma_event_id`; event ID: `1202053`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 204 | changed | Will Natural Gas (NG) hit (HIGH) $3.20 Week of October 19 2026? [market=5789201; condition=0xcb079b541d504b939fcd5959a40b7ca814babeb084f9e3a0035347422121cf2e] | Yes=0.48, No=0.52 | best_ask, best_bid, no_price, yes_price, outcome_prices | True | `9826928c9de7884f1dc67343ecab6cc9d41782b3494d84fcc2853834e04e4d0e` |

### What will Micron Technology, Inc. (MU) hit Week of October 19 2026?
Group basis: `exact_gamma_event_id`; event ID: `1202043`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 205 | changed | Will Micron Technology, Inc. (MU) hit (HIGH) $960 Week of October 19 2026? [market=5789059; condition=0x9df6b895ce98ac62ca64e410b98c80e1595d9c63e4eaf1b6ee9021af8ff5fb78] | Yes=0.37, No=0.63 | best_ask, best_bid, no_price, yes_price, outcome_prices | True | `c581cb011d8c3a9e6e59c89a268927c8880359ec1149d75aecbfb257c086c8ed` |

### What will Rocket Lab USA, Inc. (RKLB) hit Week of October 19 2026?
Group basis: `exact_gamma_event_id`; event ID: `1202037`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 208 | changed | Will Rocket Lab USA, Inc. (RKLB) hit (HIGH) $56 Week of October 19 2026? [market=5788980; condition=0x52303313b1f8f1740d0afee1c820cfa06312aab09b76d41565ff93d97aa49ba7] | Yes=0.385, No=0.615 | best_ask, best_bid, no_price, yes_price, outcome_prices | True | `b47f215dd676a9b4fc040cf66bd03219b8297f51a6e2d718138120d7ce50bda0` |
| context | context_unchanged | Will Rocket Lab USA, Inc. (RKLB) hit (HIGH) $60 Week of October 19 2026? [market=5788977; condition=0xb86e0906d140efc2b79d040b04aeed71dc9704a4c3b3d2f3e067d821e2250d30] | Yes=0.115, No=0.885 |  | True | `857f809ae4edccf6f20fe6658cb3659110fd5ec0e65e00a351c5d6255ec81f0f` |

### Military action against Saudi Oil Pipeline (East-West) by...?
Group basis: `exact_gamma_event_id`; event ID: `1147445`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 210 | changed | Military action against Saudi Oil Pipeline (East-West) by October 31? [market=5401795; condition=0xa0153e80ca43943d065a76b0c60dddc2595ceb74ed4f6b9c49335e58c639f802] | Yes=0.25, No=0.75 | best_ask, best_bid, no_price, yes_price, outcome_prices | True | `474080d7aee1961ed14a9811ab320f35315509cd0434e3609c6bdeb48b851b17` |
| context | context_unchanged | Military action against Saudi Oil Pipeline (East-West) by November 30? [market=5401796; condition=0x9e69d69cdbccdef7f8543d02dc2a60d299121286463cc5bbaf57b0aff5693a68] | Yes=0.415, No=0.585 |  | True | `f192828ed8ab13d45e2d402dea9e7018cec4680ecb381e864cc195ed6af0abd2` |

### How low will 10-year Treasury yield get in October?
Group basis: `exact_gamma_event_id`; event ID: `1116490`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 213 | changed | Will the 10-year Treasury yield dip below 5.00% in October? [market=5194813; condition=0x23a70a0548693c7e2d852dc3000176c13dd26646dd2f587403b0898ce7679df8] | Yes=0.365, No=0.635 | best_ask, best_bid, no_price, yes_price, outcome_prices | True | `31e0c3f02a25a91c8ca71e0407a237b90a0a4123fd94879a353bcb6dbcb91662` |
| context | context_unchanged | Will the 10-year Treasury yield dip below 4.90% in October? [market=5194815; condition=0x14967f8ee38445a99c0f3bbb51f4bdae280828f0fc4433f1281c54fdaa3aac6a] | Yes=0.1465, No=0.8535 |  | True | `725b74eb0e4873d66f04655fd189198d09cdf03d6c61c4e7936523fd1ee470ab` |

### US-Iran Hormuz Agreement by...?
Group basis: `exact_gamma_event_id`; event ID: `794064`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 214 | changed | US-Iran Hormuz Agreement by November 30? [market=5087226; condition=0x2b9931e13d436ee68b2870d31400f5bed8f5f13ad321355d0fd1048f706bba6a] | Yes=0.36, No=0.64 | best_ask, best_bid, no_price, yes_price, outcome_prices | True | `69224817c57fae85d00c459bccfca6caf557a05fef2d7b5ca55065c962a4a348` |
| context | context_unchanged | US-Iran Hormuz Agreement by October 31? [market=5074920; condition=0x0038a19c5f1633b76e9fe194ac391959811cceb05652ba5c6796e37f045e573f] | Yes=0.118, No=0.882 |  | True | `62ae21c2ba4dfe3fe88266b3296cd79a2c0bf44e94e093fd685843f5c8d98c32` |
| context | context_unchanged | US-Iran Hormuz Agreement by December 31? [market=5087228; condition=0x664f36528d54361c2579fd5ddc8072a831e7039ac849615d6aafcafd256aa9ec] | Yes=0.38, No=0.62 |  | True | `3142484ff7200c7e41a2c8188f23b007916e91869e13e39f4459625aa09640bb` |
| context | context_unchanged | US-Iran Hormuz Agreement by November 2? [market=5571194; condition=0x1e48a0d3f791a763e5efca1479ed1d63e96aa6d00107ee142e829e32e88154db] | Yes=0.1625, No=0.8375 |  | True | `44e5a8d00347d36508d60fae2bb501291a72360fb531ccda4ce0b06ac5b23c8f` |

## Batch 31 (19 markets)

### Democratic Senate odds on October 23?
Group basis: `exact_gamma_event_id`; event ID: `1194282`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 216 | changed | Democratic Senate odds 62-64% on October 23? [market=5731327; condition=0x65b1b87f6f1fbd5ce524d979b83de93f23e45c9626b48129bb114a2f3cbe70a1] | Yes=0.44, No=0.56 | best_ask, best_bid, no_price, yes_price, outcome_prices | True | `80a7934c071a0f825bb8423c4e56e19e8817b7e252e29d5fd3e9d5ef840ce8b6` |
| context | context_unchanged | Democratic Senate odds <58% on October 23? [market=5731324; condition=0xb49545e04ee8130e2ba7d52326330329d6411e53757c1e102746e2917b504aeb] | Yes=0.006, No=0.994 |  | True | `133005f9acb4067a64c174004edb29a5f61014da50fed4f70c518dc380bc4138` |
| context | context_unchanged | Democratic Senate odds 58-60% on October 23? [market=5731325; condition=0x7e33e195ce61803c71a811bbecec6134e1ee90fff769e648a799b2dbc2939f00] | Yes=0.0085, No=0.9915 |  | True | `1bbb1ac6572612561da68b8d385d1e6de766203ae4eed364560d82d054ad9519` |
| context | context_unchanged | Democratic Senate odds 64-66% on October 23? [market=5731328; condition=0x8ce74531ec557ef56ebddf9f31199610a909c61a36ab7e6e236a6e2439c28c6a] | Yes=0.335, No=0.665 |  | True | `db38507a8960e8a947540b98ad4c9c3751228a2a0ebc789057275a44e9d9b9ce` |
| context | context_unchanged | Democratic Senate odds >66% on October 23? [market=5731329; condition=0x725ae8c2b348bc1b7abb2151d59e85c130ca76412cdb5da1cb0bd35f4d38704b] | Yes=0.195, No=0.805 |  | True | `2502fe5b936987267bc8625c431a0509380e60d24d5376e5216d686bea23be4c` |

### US-Iran ceasefire continues through...?
Group basis: `exact_gamma_event_id`; event ID: `1038648`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 217 | changed | US x Iran ceasefire continues through October 24? [market=5686977; condition=0x8cd2457d67e7c9260161f6307ec7c4dde35217b94dbe7959c0ef9d0a63f7344d] | Yes=0.725, No=0.275 | best_ask, best_bid, no_price, yes_price, outcome_prices | True | `7b53f8efc4ad644e8b7b2f2fe5df631cff12fe34c787c14fb7f2cab41bdcb658` |
| 222 | changed | US x Iran ceasefire continues through November 15? [market=5190747; condition=0xc83347e2b7a1d1341cba0fc6d03696c3be31c783b732355a04c8f8621ef4df09] | Yes=0.43, No=0.57 | best_ask, best_bid, no_price, yes_price, outcome_prices | True | `47a9c77294cf6b1c73f0df0d10eb36bcd4325d046210dec3f830bab96b0906b2` |
| 223 | changed | US x Iran ceasefire continues through November 30? [market=4713483; condition=0xb70b8da7839ecb8b166e0f3a8553e079b38e139ee164f5d8bfd99183d535fc33] | Yes=0.38, No=0.62 | best_ask, best_bid, no_price, yes_price, outcome_prices | True | `2598784c451871a916d4e82585e8fbe484885018de3843568f85aaffdf6e35e5` |
| 231 | changed | US x Iran ceasefire continues through October 31? [market=4641065; condition=0x3738ad9665480991affe3ba286cd035516e17d1f8b7703e05088ec19c70c21a4] | Yes=0.625, No=0.375 | best_ask | True | `9f80a705fbb60efe9ea18e1edee1b2fe66f566a43b006fe0e52bd2294c1763c8` |
| context | context_unchanged | US x Iran ceasefire continues through December 31? [market=4713484; condition=0x32851891e7ccfb249b1e120d77db70370fa92a13d821ce6c949de69402742aab] | Yes=0.295, No=0.705 |  | True | `ec115a535b3a0d458290cba4d7eb925ca7a3f36d06d795faf482d0600f0d7391` |
| context | context_unchanged | US x Iran ceasefire continues through November 22? [market=5686978; condition=0x59ddc2932f49564467e41975f22552c5e73a9517a31593a97125b9c0e9040632] | Yes=0.395, No=0.605 |  | True | `24f0572a6e2ce41d4503ecd81632cd0bcf8d00d3772b4aeaf336afd7e2bd1ed5` |
| context | context_unchanged | US x Iran ceasefire continues through October 22? [market=5686979; condition=0x04fb634139d4654febf4b62c425b209806e06d9eff93ac2e7c5301ecdaf5e4ca] | Yes=0.7395, No=0.2605 |  | True | `7169d5cefc7e3cbea8f29a8854a965693341f50f73d02090b14458a1d82dcdfd` |
| context | context_unchanged | US x Iran ceasefire continues through November 8? [market=5686980; condition=0xdbcc19248725b32aa85acbdd91f1877cb124a68cf6d7bc2d036e0e91ffa0f9c6] | Yes=0.56, No=0.44 |  | True | `1466baae8f51451bf1d77518bac11d27fa4a2e9b06b7e0ef4901c3a484e7a9ab` |
| context | context_unchanged | US x Iran ceasefire continues through October 28? [market=5686982; condition=0xff019ccfa1337dc7d12968183949ff5877a8b66ab19903e42331a7b94f97cfd7] | Yes=0.695, No=0.305 |  | True | `7b923539ad0b9f60c97099fb59f8cab38d7642b794bb7eecb4df507d985092d8` |

### NY-04 House Election Margin of Victory
Group basis: `exact_gamma_event_id`; event ID: `834407`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 220 | changed | Will the Democratic Party candidate win the 2026 NY-04 House election by 15%-20%? [market=3519820; condition=0xc61008cbe99f5d1011d597b3e0622be07976a9e561dd9d43910364974133b6ec] | Yes=0.185, No=0.815 | best_bid, no_price, yes_price, outcome_prices | True | `b7c98503d78aaa9435806c7eeb8f683999a99b2d24be5ffb20d6d2e9ed44985b` |
| context | context_unchanged | Will the Democratic Party candidate win the 2026 NY-04 House election by 30% or more? [market=3519817; condition=0x22e7bb062a2bc9ac4bc0a99867b37f48908e6816b0b8d2619b7ce4d5f1c343bc] | Yes=0.011, No=0.989 |  | True | `1a04c88a70599b7b0ef95f5a77435d69778f6b38c43709362e792fda6f174fbe` |
| context | context_unchanged | Will the Democratic Party candidate win the 2026 NY-04 House election by 25%-30%? [market=3519818; condition=0x8e7a35fe4a6b29f8ac54f518d7976894f857e2513568fee832f80fafa4b55bff] | Yes=0.042, No=0.958 |  | True | `afe787362dfa81a8ee47d9ba65d1518fb4dd3ac8bad5ba87009754bbf17cc0d7` |
| context | context_unchanged | Will the Democratic Party candidate win the 2026 NY-04 House election by 5%-10%? [market=3519822; condition=0x9a230fd01d3dd1c65dbe266e1819e31d9665f89923c8ce68e7c629015df24a44] | Yes=0.1525, No=0.8475 |  | True | `7e5e89c54301814c2eb3f5b5c6f2ab23d2fd273088fc1c39859d16964cf2b4a6` |
| context | context_unchanged | Will the Republican Party candidate win the 2026 NY-04 House election? [market=3519824; condition=0x669c8af4bf41cf25899ad46aa3a1473bfdd41c2f84bb7714a860ba8d2430f92b] | Yes=0.0615, No=0.9385 |  | True | `aed51483906e2f3e0b6785709c1153cedce3fa2d646f25ebed389281fc9ab905` |

## Batch 32 (19 markets)

### # of views of Grand Theft Auto VI Launch Trailer on week 1?
Group basis: `exact_gamma_event_id`; event ID: `1194438`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 224 | changed | Will "Grand Theft Auto VI Launch Trailer" get between 60 and 80 million views on week 1? [market=5732710; condition=0x5d3143945da3dc365e94e0e162d8b93210d0ac1546b1b5b138702cbf627a7ad0] | Yes=0.3285, No=0.6715 | best_bid, no_price, yes_price, outcome_prices | True | `0639d74e7af2d23bf02a71767e78c72ff3031598d9fafdfbeda460c0aa70dfd4` |
| context | context_unchanged | Will "Grand Theft Auto VI Launch Trailer" get between 40 and 60 million views on week 1? [market=5732709; condition=0x15114829ad5587c8a328c574a12a4bb7322901dcc2d3a7f546cbfd4f3cc14d10] | Yes=0.645, No=0.355 |  | True | `8c5badeac51fcc3090946fe1c38925ab9c867de76f9d2547982488c661a7baae` |
| context | context_unchanged | Will "Grand Theft Auto VI Launch Trailer" get between 80 and 100 million views on week 1? [market=5732711; condition=0x3e97e02a156a2b1424a7196e45582238e9d0da90c98602723e37e9e085075909] | Yes=0.0065, No=0.9935 |  | True | `d3a8d31024d86db3d532888fa345361274a01b92733925e1e284be1d1199b622` |

### Ballon d'Or Top 2 Finish 2026
Group basis: `exact_gamma_event_id`; event ID: `1189431`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 225 | changed | Will Lamine Yamal finish in the top 2 of the 2026 Ballon d'Or? [market=5693684; condition=0x73342d74c5c6975ea3b717f1d061bd2afbd787858c556ff6c801119e0290df31] | Yes=0.345, No=0.655 | best_ask, best_bid, no_price, yes_price, outcome_prices | True | `476382bb188b3dd8c144150bb4745b356e7d1db425eaddfb5e54d5ba489536be` |
| context | context_unchanged | Will Fabian Ruiz finish in the top 2 of the 2026 Ballon d'Or? [market=5693689; condition=0x19d901aeb423106d3d696ed67546b3b8405543290d573b830bcfc8e84463ea15] | Yes=0.015, No=0.985 |  | True | `962cd271f3d7328ca224e3dd7dedb0a9bf4736b755a73c1769f1fe8d1d8c3ffa` |

### Next James Bond actor?
Group basis: `exact_gamma_event_id`; event ID: `498879`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 226 | changed | Jack Lowden announced as next James Bond? [market=2293863; condition=0x490b4abcc5b23958f5515716fbab843574f9cffef4bc52eac3a3939809757b46] | Yes=0.243, No=0.757 | best_bid, spread | True | `2b012fe40451d78047106a7e6655d8877afdfc15d923bb8c21c8197e01aa9ada` |
| context | context_unchanged | Paul Mescal announced as next James Bond? [market=2293854; condition=0x1d6b738eec27296a3add3fd93de0a59aa61a3cc467b76b912ab1a931b4cd0436] | Yes=0.0135, No=0.9865 |  | True | `bfe01ff3e9d104a86aec7733df904c92395641efc7d3366f8724f2487607a57f` |
| context | context_unchanged | Tom Hardy announced as next James Bond? [market=2293857; condition=0x6522a47a9d908d3f7667044c4de2621d78319bdca65266e6fa933caa2366b64a] | Yes=0.0085, No=0.9915 |  | True | `5bb7d9606fdc160a190215f267a8b71880fd89cb54430a7079f5e3b759e257ef` |
| context | context_unchanged | Callum Turner announced as next James Bond? [market=2293862; condition=0xdf55222217299506bd9b7b348ac3be51137ac480da920567722824f0c40c5fc0] | Yes=0.1805, No=0.8195 |  | True | `5227df24d7666bc8187fc192a2727e68115253bfddbf6104f9f66c415da5ca13` |
| context | context_unchanged | Josh O'Connor announced as next James Bond? [market=2293866; condition=0x7de7918ba7be54764ec10958af792776d0dc2f77bff0d8aaaeac7c6f97015b77] | Yes=0.0515, No=0.9485 |  | True | `9ede258670771613e42f8e6157520b9d9c15a1ea4da11847dc8a32508b162e8b` |
| context | context_unchanged | Jack Barton announced as next James Bond? [market=2293870; condition=0xabb40a75a60ffd8e6c124e6d1eaa15bcf0546b7c519f76ab989c14a32f7e0d2b] | Yes=0.0495, No=0.9505 |  | True | `64d54a9dd7f3b52f4625b97f64041a81d3f8d276f697d55eb8d498fff639158e` |
| context | context_unchanged | Tom Francis announced as next James Bond? [market=2293872; condition=0x64373a7da83808eef16871d343d682739210c6731c1d75e77ca6a91a3b3130c7] | Yes=0.03, No=0.97 |  | True | `4e0081adee8b0d125a2c79ca03546543a1fcadecb17c8e345e12f9aa0859a95f` |
| context | context_unchanged | No one announced as next James Bond? [market=2293900; condition=0xdfd9e88f948c6875027c881dcb50daf56ae577b0e4c4349779e7bd448ddc3a0b] | Yes=0.3785, No=0.6215 |  | True | `a477be9961ca5aa31075c0176a15b218b59f8cff38f27942dc732ec215332b1d` |

### Anthropic IPO by __?
Group basis: `exact_gamma_event_id`; event ID: `549019`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 228 | changed | Will Anthropic IPO by November 15, 2026? [market=4319440; condition=0x94ae8e5414e036e2e9b6b6514c048042bf74d089614d7f7d73635693f9d5186b] | Yes=0.103, No=0.897 | best_bid | True | `3255e0e8707e4daf3d9e3541a3d155c94dff59ffb9954bfae1618f192827d278` |
| context | context_unchanged | Will Anthropic IPO by December 31, 2026? [market=2413330; condition=0xb40b0cd531184a1e436d23ca898e1590418187b116f387158753d1adb9853e47] | Yes=0.765, No=0.235 |  | True | `9dbcc69348422381981004056439dea7966e95a2b00640cfa90ca072d44e264c` |
| context | context_unchanged | Will Anthropic IPO by October 31, 2026? [market=2421094; condition=0x8062cf78d93f9202f4c0a1018d141f4af35d486a368f07e65265f27d48b4e040] | Yes=0.0025, No=0.9975 |  | True | `839109ac4e3b43bb9695cf082ad97bb0994ecfbc20c40fe11f05acddeb01db2a` |
| context | context_unchanged | Will Anthropic IPO by November 30, 2026? [market=4319439; condition=0x5ba72dca702ddf6ac8ce0b992b521dd3b080109e39a5f022827ffda3ac8a60f6] | Yes=0.635, No=0.365 |  | True | `899840c9e4d6f226a5e92ad5a82b2b2682389e7821354b8f90d29aed733d2d8a` |
| context | context_unchanged | Will Anthropic IPO by December 15, 2026? [market=4319441; condition=0xd840a4faf46b63d0be3f7918e8014fd848e396fdd76f2554f1497fb3553f8010] | Yes=0.755, No=0.245 |  | True | `d7317d6c1d9edf2c1458fda9211de7376e134d416efea893e9dd3ff09c5e2d29` |

### US-Iran ceasefire continues through the midterms?
Group basis: `exact_gamma_event_id`; event ID: `1156710`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 232 | changed | US-Iran ceasefire continues through the midterms? [market=5447182; condition=0x613613192c69d90cee89758c260a019368fc1f4a596b4d300c39b6235d2b643f] | Yes=0.63, No=0.37 | best_ask | True | `a35ea08362d004cfd645499651bec8abe6d3b4503071f2d8d1b321bffe5b53d9` |

## Batch 33 (20 markets)

### What will Gold (XAUUSD) hit Week of October 19 2026?
Group basis: `exact_gamma_event_id`; event ID: `1202050`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 234 | changed | Will Gold (XAUUSD) hit (HIGH) $4,200 Week of October 19 2026? [market=5789159; condition=0x49e22efba5988f43812671f15e6ffeeab533744f140506dc751f2ff1cab80936] | Yes=0.495, No=0.505 | best_ask, best_bid, no_price, yes_price, outcome_prices | True | `c358c037ba8b421518b39879ca015e889521e04075a24a4c08abaa08695a5e8d` |
| 235 | changed | Will Gold (XAUUSD) hit (LOW) $4,100 Week of October 19 2026? [market=5789161; condition=0x04eb66d0976526fdd5866c3872f0ba8d470ae585fc56ffc7bcf6dfaf5a27cda9] | Yes=0.65, No=0.35 | best_ask, best_bid, no_price, yes_price, outcome_prices | True | `774ab8d2241edd6d72df978d2983cd340866e75be6f4885982b9e43e23a7f94a` |
| context | context_unchanged | Will Gold (XAUUSD) hit (HIGH) $4,400 Week of October 19 2026? [market=5789155; condition=0xe02b70fb7233df4161d33e48f72813c607b9234f12f9acfc5e454bf886ab43e4] | Yes=0.02, No=0.98 |  | True | `52f2921a4b8625eb7d825b87612b86e5018c17966a00df06e21f6cad9ec24e18` |
| context | context_unchanged | Will Gold (XAUUSD) hit (HIGH) $4,300 Week of October 19 2026? [market=5789157; condition=0x9438ec14e9833bea793f07460840d2b31c4ca5c2233dc3d145f93b8b41035cee] | Yes=0.105, No=0.895 |  | True | `91742e8a537d594d0a497bd52d60a279c61a7c82ddce3ba55ddd3b59bc73e672` |
| context | context_unchanged | Will Gold (XAUUSD) hit (HIGH) $4,250 Week of October 19 2026? [market=5789158; condition=0xa28b4de17b72bbf292c5213b9d38143265c049a863421fc88f9f262a9329e90d] | Yes=0.24, No=0.76 |  | True | `6330d88d4a0dfc9adf425cef29dd563b8568f58bc16ccd328a8694f4330cc60a` |
| context | context_unchanged | Will Gold (XAUUSD) hit (LOW) $4,050 Week of October 19 2026? [market=5789162; condition=0x74e49970f174e71775e9390ddcb24227e2b47d47287f242aab54543ef57fa1a9] | Yes=0.335, No=0.665 |  | True | `f1bf008b2d430a6297427aef4b05efb441e34982f740b2494c625935d1fe33dd` |
| context | context_unchanged | Will Gold (XAUUSD) hit (LOW) $4,000 Week of October 19 2026? [market=5789163; condition=0xe7e453a658ce66aa15f22ab0a8fa55c7f75012871567ad1ebf04ca122d775b90] | Yes=0.145, No=0.855 |  | True | `f975d327923908e083512e603c2224f44b31975a4d1743a3c524363404d9ef5d` |

### Who will attend a round of US-Iran peace talks by December 31?
Group basis: `exact_gamma_event_id`; event ID: `841086`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 237 | changed | Will Badr bin Hamad Al Busaidi attend a US x Iran diplomatic meeting by December 31, 2026? [market=3553894; condition=0x5c5d128039632bafae6e04840b767fc8e09fc968db7492a09d462c15e4281c9e] | Yes=0.16, No=0.84 | best_ask, spread | True | `1e20c5017e156414af42bf87ed6adac2901833608b4a82c7f89fdcfc80aa8867` |
| context | context_unchanged | Will Marco Rubio attend a US x Iran diplomatic meeting by December 31, 2026? [market=3553881; condition=0x279311babfe66de1128989f88ce24468cda94e95d8f3b80ba1a465ee851e0cd7] | Yes=0.085, No=0.915 |  | True | `cead6bd514d63294e51899d1ec792b4e339d1cc3c9c4a4f93c1671f4ac8b5e66` |
| context | context_unchanged | Will J.D. Vance attend a US x Iran diplomatic meeting by December 31, 2026? [market=3553882; condition=0xcf7d94c9aa083c8235103832dc28e4b85d4436a58453fcdfec2ff2e21c4b10cb] | Yes=0.17, No=0.83 |  | True | `846a7c62aaaf6668d28e9a3d597d35ca2e8c7d08d7c30b3dbacbf6d82155f51c` |
| context | context_unchanged | Will Mohammad Bagher Ghalibaf attend a US x Iran diplomatic meeting by December 31, 2026? [market=3553887; condition=0x0d0cc122d45ae32132dff864936e8d4e58ee68231034d9114eb92e8958bd3899] | Yes=0.23, No=0.77 |  | True | `327842bedd34666429870f599c5d183882955bf59adc9ede24ea5bb9f046c0b0` |
| context | context_unchanged | Will Masoud Pezeshkian attend a US x Iran diplomatic meeting by December 31, 2026? [market=3553889; condition=0xa7237f7d6b9175aa6a12e3b276ef6f14eb3301df3cba1ae5faf30008f2dabf44] | Yes=0.13, No=0.87 |  | True | `43e651b3f6c9298bdff4cc4a1027050799210e7e90041c5146b5b1781440ffdd` |
| context | context_unchanged | Will Majid Takht-Ravanchi attend a US x Iran diplomatic meeting by December 31, 2026? [market=3553890; condition=0x6dc48af20a509575041a8bc3694c1f259f6054dc6835a9dcd73abf879b416459] | Yes=0.26, No=0.74 |  | True | `4fe57a50eadaf68be7851345f8689908c33ca3979493ee73bbe19fa68782eff7` |
| context | context_unchanged | Will Kazem Gharibabadi attend a US x Iran diplomatic meeting by December 31, 2026? [market=3553891; condition=0x42d86517194ccb44fc99732d796f416ae6850d28b91d10210b3bb094639735d9] | Yes=0.23, No=0.77 |  | True | `c49a7207ee0d615747f0483908821437192ce4ca9643c6a12946618ea97553c9` |
| context | context_unchanged | Will Ishaq Dar attend a US x Iran diplomatic meeting by December 31, 2026? [market=3553896; condition=0x19511a0e3a94a4329f718cc4162dbf152b57e10c901d21d202cd9e8de9ef5c44] | Yes=0.135, No=0.865 |  | True | `0c0dee48e001853bd1ce05d298f64bf4839c05b4999f9ec579f32886096bba41` |
| context | context_unchanged | Will Nick Stewart attend a US x Iran diplomatic meeting by December 31, 2026? [market=3553898; condition=0x58cfba38bf5b62260918d3e77da04ac8e8135c48a36802373e4c0eefc7676569] | Yes=0.29, No=0.71 |  | True | `3abba950fd94d0d186ee331274913a79f2261b755429447181a463cf5d44569d` |
| context | context_unchanged | Will Steve Witkoff attend a US x Iran diplomatic meeting by December 31, 2026? [market=5191216; condition=0x81fac61f26f6b2ad9355952a8daac80e6939f39431e5c263dfd6532d4607ca24] | Yes=0.36, No=0.64 |  | True | `0e91331637104a45dcd31d6d65fb8abe2214ca65c898b48ca0624e5fa943fe5c` |
| context | context_unchanged | Will Abbas Araghchi attend a US x Iran diplomatic meeting by December 31, 2026? [market=5191217; condition=0x77c98ebeb0a79430cbf8d28ff418efa204ae54ca987217e4e1a921d6eb0bdeba] | Yes=0.35, No=0.65 |  | True | `ff321de55deaa5824f7825a08ecc7118abdb42e792a098c0044f6cd50bac3c16` |
| context | context_unchanged | Will Jared Kushner attend a US x Iran diplomatic meeting by December 31, 2026? [market=5191218; condition=0x2494c4a26f40f76e142d0293953239e175dca2a2e8395baf022fa1427984d97f] | Yes=0.37, No=0.63 |  | True | `e4276959598a560b3761c68da400c83c6798d83071dda3dd8c6b3af1e3fddad2` |
| context | context_unchanged | Will Mohammed bin Abdulrahman Al Thani attend a US x Iran diplomatic meeting by December 31, 2026? [market=5191221; condition=0x0c1a3eed16beeba8929f58dfc9688dd98bad8404f2b3acf0059efda69fa5d460] | Yes=0.275, No=0.725 |  | True | `5b6d017e5c53eca4ff635909d24922ae04775460f959aa828985af51aaac185d` |

## Batch 34 (19 markets)

### Will Variational launch a token by ___ ?
Group basis: `exact_gamma_event_id`; event ID: `73902`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 238 | changed | Will Variational launch a token by November 30, 2026? [market=4913661; condition=0xb06951a69f76c15116e4987d6163619e5d062f6857ee3d35ddf0e09d76b2a13b] | Yes=0.24, No=0.76 | best_bid, spread | True | `f04abcc345913ef40ed8a6ae10ae11ae0dae224f4922cb6dbe1f659213c54bd5` |
| context | context_unchanged | Will Variational launch a token by October 31, 2026? [market=4913662; condition=0xbf1ea06dacf40b5537113b7e676426d427acfdf793df7bc58a3a6754af59d06f] | Yes=0.0255, No=0.9745 |  | True | `aec74780cf98b64082a96229fe2684cfe0de890a8dab64b8954542e9f1892107` |

### "The Hunger Games: Sunrise on the Reaping" Opening Weekend Box Office
Group basis: `exact_gamma_event_id`; event ID: `1191150`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 240 | changed | Will "The Hunger Games: Sunrise on the Reaping" Opening Weekend Box Office be between 75m and 85m? [market=5713554; condition=0x43ec89c2e065f512f18e941cdff94158ede6ddc57591cb21e4d252a931fa7d10] | Yes=0.2, No=0.8 | spread | True | `abd88f5a4438c3c6d09f5d1356278774c5956f43a0f07caafa076b9bc56adf6a` |
| context | context_unchanged | Will "The Hunger Games: Sunrise on the Reaping" Opening Weekend Box Office be less than 65m? [market=5713552; condition=0x0c67af31f2b335b7d347d3f64930464635586e5e87292fc22ce17b176a763dcd] | Yes=0.285, No=0.715 |  | True | `638f644cf980778dcb3ffbe1eca61d5ab379f5cc9690dc6342895bab917844c6` |
| context | context_unchanged | Will "The Hunger Games: Sunrise on the Reaping" Opening Weekend Box Office be between 65m and 75m? [market=5713553; condition=0x6d7b7bb1411775c6f4123105d266e4cf1bc182ff49b6ec556eb855c9b512d83f] | Yes=0.225, No=0.775 |  | True | `781f9547128594bacde299dbb065ab3936bd47ddf91d428c675e7e759e4700be` |
| context | context_unchanged | Will "The Hunger Games: Sunrise on the Reaping" Opening Weekend Box Office be between 95m and 105m? [market=5713556; condition=0x3b79cc53bbbccf8b67982e1912163b1ec53ff910b64b787591d29fe93bf27665] | Yes=0.105, No=0.895 |  | True | `01eb1a74ed817e5a66a2515e1f21d3e80f2a5e35b597013005448a2efa3646ae` |
| context | context_unchanged | Will "The Hunger Games: Sunrise on the Reaping" Opening Weekend Box Office be at least 105m? [market=5713557; condition=0x80092748ef14288632ad9a10356b467c996afddebc04aa06cad3b16d2dd54f95] | Yes=0.155, No=0.845 |  | True | `726d536f5705cd4f2ae0dbe497919a03b30e9a82f0f7809f1bb7723200873fd9` |

### What price will Solana hit in October?
Group basis: `exact_gamma_event_id`; event ID: `1112223`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 241 | changed | Will Solana dip to $100 in October? [market=5170805; condition=0xba2998f8288f2b245045eee70b23826aed61847f0fd19bb291655f553a97923a] | Yes=0.68, No=0.32 | best_ask, spread | True | `af754955f5821621c61026800b5c829dcb32fadbfbff86ffcd22fe1aeb4462b5` |
| context | context_unchanged | Will Solana reach $200 in October? [market=5170795; condition=0x8656e336f5c0a9e23025e29473e42745e8ea90a3b91cf27e87079813d003d50b] | Yes=0.0035, No=0.9965 |  | True | `2518eda9e6233edb9f09fe048028f41beb6d4313cebfd5a6d47869903fac48c0` |
| context | context_unchanged | Will Solana reach $170 in October? [market=5170798; condition=0x9dbdd73e66238d241c2f8c5f9373d7ce81068582af47d76fec1b94ce1e31f4f1] | Yes=0.0125, No=0.9875 |  | True | `5e88e584b51af35b6288774db12f412616b7fb98528a353482446418c90f0374` |
| context | context_unchanged | Will Solana reach $160 in October? [market=5170799; condition=0xed510d74352415439fbef45a3e034f637754ed4a06f7a2a91c555b76edad5e56] | Yes=0.0185, No=0.9815 |  | True | `166d1c01742d40c7e1910482133e71f46e349468aa1116afcfa66ef741475004` |
| context | context_unchanged | Will Solana reach $150 in October? [market=5170800; condition=0x5e242c3bcbb02f4e4222df8467ffa31693403d2c7d429de5467438ca482f8129] | Yes=0.0215, No=0.9785 |  | True | `11ca0abfa313b410d130176e0ae23b28ef62df3c6df4d9b766f0be901047fb16` |
| context | context_unchanged | Will Solana reach $130 in October? [market=5170802; condition=0x752736974c97a2e83db55ceea85ab0cda576dfded4dc4b6ec72d56b39c18aaa3] | Yes=0.065, No=0.935 |  | True | `8e931e2212a24d442934a3b63e0372029dd84cd4348b2f641991c5924ceea988` |
| context | context_unchanged | Will Solana dip to $90 in October? [market=5170806; condition=0xf8ee7fb235671f2a205911ddc42fdfac9c2d93b125f023371760e29196bf96e9] | Yes=0.195, No=0.805 |  | True | `ecd9747ef367f6fdca5add3d9d40e0aa0352823201724dc1bc74cd581d1dd5f1` |
| context | context_unchanged | Will Solana dip to $80 in October? [market=5170807; condition=0x25ede9e5749af8a0deb9a3077f222183dee4b8f9b65638675eaeb51c5ec97d4b] | Yes=0.0375, No=0.9625 |  | True | `31fde3a3b850211ef09ddd203ea2cf32990a34ddcb53b726dc54c0c16a4d96fd` |
| context | context_unchanged | Will Solana dip to $70 in October? [market=5170808; condition=0xa0237dca454b35312cc210e4711122b0a5254fef11b7077db5c892ef7a1498a1] | Yes=0.0125, No=0.9875 |  | True | `a861e2fb2b9bd11a494e18fe5f70a5e03a9a75591f654812fc4aaba3abe9eaf1` |
| context | context_unchanged | Will Solana dip to $60 in October? [market=5170809; condition=0xc76def9daa589a5dd198665764a7913afc15f22f8c93b3c59b742fc56ffb52a9] | Yes=0.0085, No=0.9915 |  | True | `7de8275115337fc88a97eb848426f4eeb5d09b307537bde90ef4c958870f0193` |
| context | context_unchanged | Will Solana dip to $40 in October? [market=5170811; condition=0xf93fb86abf4cb96f1366404b7e494b1c03ffa7b076f7ea387cdbe222533732be] | Yes=0.0015, No=0.9985 |  | True | `62ed073bcdf6b8335f0d66afc966ffaa4a1c2fd5849e4ba04e8ccd1255ecd8d6` |
| context | context_unchanged | Will Solana dip to $30 in October? [market=5170812; condition=0x977cd0540918b9953260b26bff4acc9c48fccf492da3a7ffaaf26a93ab98393f] | Yes=0.0015, No=0.9985 |  | True | `1edf26937d4d9bf4633a2b563b747c84da7e0dd2a4bca73f74ef43b43792032f` |

## Batch 35 (10 markets)

### Next leader out of power before 2027?
Group basis: `exact_gamma_event_id`; event ID: `653446`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 242 | changed | Will Kim Jong Un be the next leader out before 2027? [market=2750300; condition=0xc41ec7ef46aeaf92c52a0e47fdaae094064d58efb9c5e3c73694d282bdb0ef6b] | Yes=0.02, No=0.98 | best_bid | True | `c3c23f8143c1e9e0e35105a7c9077b69426f4f20f03a5a2613c66208e9a7b10c` |
| context | context_unchanged | Will Emmanuel Macron be the next leader out before 2027? [market=2750298; condition=0xa269db945d01305fc42b3bfa3e01e95ee17619a5e490e26236d969401c79e2ec] | Yes=0.0105, No=0.9895 |  | True | `fd74c6ed038e07700dceabe96f7f5889ea64fc1a4c57b72e780da9b83acf3ec1` |
| context | context_unchanged | Will Benjamin Netanyahu be the next leader out before 2027? [market=2750302; condition=0x780fb498b1f10fe785545ab25b2129398fe8fca4fac25471f37884d02264fc09] | Yes=0.305, No=0.695 |  | True | `1297d1709ff82f20f17400cb8aaca7a0d050b8c771f821d733e205115b6a474f` |
| context | context_unchanged | Will Volodymyr Zelenskyy be the next leader out before 2027? [market=2750307; condition=0xdf32503b14fe232043d9db63ae787db13ddbc8374f4d1d016fd7d90d68e87147] | Yes=0.0115, No=0.9885 |  | True | `5cdbf2caa448d0425c27b77abad72371b60171a65f3868fbf9a44f6e891684e4` |
| context | context_unchanged | Will Sébastien Lecornu be the next leader out before 2027? [market=2750310; condition=0x9dadfa633cab5b1f3b7711a47d16c9e352dc57654e1b746067bae3f82214435b] | Yes=0.037, No=0.963 |  | True | `2050cfb3e513a7d0091124363b6360368687a18c1b3f5b7e9abe431337e018fd` |
| context | context_unchanged | Will Mahmoud Abbas be the next leader out before 2027? [market=2750312; condition=0x87b4fab9ba12e7ac29735b5fe63b9398a95d4e46185c55a3a52433bffae9cee7] | Yes=0.009, No=0.991 |  | True | `1ab7145acd207e382eb8f88522bad6a62d69c899fe7fb7612f01da733be6f980` |
| context | context_unchanged | Will Friedrich Merz be the next leader out before 2027? [market=2750313; condition=0x24054faa76513d7d4c87d0f7d9fe8336317da6406d05aea6e623f3aed9dd0c6c] | Yes=0.007, No=0.993 |  | True | `2dc425b91a1682946fe5aae10c1691e319e03923e75c90c76306efd9ec88ffd2` |
| context | context_unchanged | Will Pedro Sánchez be the next leader out before 2027? [market=2750314; condition=0x0ea6e9ff415871b64273a991ad7560f19d38a25449b996fa83655a5e8f818821] | Yes=0.03, No=0.97 |  | True | `25161d6fcd59aa32cef54afee88d0cc66451f04b450913eede015b2be2e3db76` |
| context | context_unchanged | Will Miguel Díaz-Canel be the next leader out before 2027? [market=2750316; condition=0x8dd5ac33cd5d2b942c3f51d519648f1bbd75e854fa77255973f034bcf51f6434] | Yes=0.007, No=0.993 |  | True | `8d0dc0b19c09f2be9cc9f74bdbb4b8d73f7da44d8b9b7e3167f19d34fd6f3e89` |
| context | context_unchanged | Will no listed leader be out before 2027? [market=2750319; condition=0x3b5a8f61120f2fb2a808f117b950d7c37ad3ee0953464ba69927c31d24cde918] | Yes=0.51, No=0.49 |  | True | `a84a4efe1ecb632ef77c4093cfc89b3dff63beff55253d4b772079569b0e6d00` |

## Batch 36 (16 markets)

### What will Silver (XAGUSD) hit Week of October 19 2026?
Group basis: `exact_gamma_event_id`; event ID: `1202051`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 243 | changed | Will Silver (XAGUSD) hit (HIGH) $60 Week of October 19 2026? [market=5789170; condition=0xbf00ba6fd410f2de2d0f929d8602cc8d8c03da07a99e34ce8d50cc0f494ab36f] | Yes=0.185, No=0.815 | best_ask, best_bid, no_price, yes_price, outcome_prices | True | `b29b87ac7099bbfeca6625566d62338f2a3c597d4e7c45976933cfdcbf0ec034` |
| 253 | changed | Will Silver (XAGUSD) hit (LOW) $56 Week of October 19 2026? [market=5789174; condition=0x0d96a99509230c99fec79346036b06825b581693398650cc8676a0c34958820a] | Yes=0.58, No=0.42 | best_bid | True | `ca8d173f57655bd109be09745f01982528f6466202f79654f091f1f7a6fe7618` |
| context | context_unchanged | Will Silver (XAGUSD) hit (HIGH) $63 Week of October 19 2026? [market=5789167; condition=0xdad36d3f4987fe01d79083182bb6aa204b8a6394df865babcdcd285d5fbdc55f] | Yes=0.033, No=0.967 |  | True | `b18af9c37d8ca37d6d96c883203330fba26f65222ee3e93467bc22ada929c83c` |
| context | context_unchanged | Will Silver (XAGUSD) hit (HIGH) $62 Week of October 19 2026? [market=5789168; condition=0x36044e721eb8e10c2eae1c3fb39dd5717358792af10dfe462813f7fcebddbd5d] | Yes=0.065, No=0.935 |  | True | `622a4fe967ba2faa11066008eb67a008246867289c2b5d21cd148436f383b99f` |
| context | context_unchanged | Will Silver (XAGUSD) hit (HIGH) $61 Week of October 19 2026? [market=5789169; condition=0xf327e56386582fcada8cec458d33d793bb82d5e679df936e048f3e5b17708642] | Yes=0.095, No=0.905 |  | True | `864edb2211d76e7da67f5b6bac4afd5b10459b6de1016bd25fcca6e2bd871b67` |
| context | context_unchanged | Will Silver (XAGUSD) hit (HIGH) $59 Week of October 19 2026? [market=5789171; condition=0x0374366ff66ec3be05edc678726c8fd9918cba068faffc21133d42a9516a361b] | Yes=0.4, No=0.6 |  | True | `6a5ccc8c213527fb8c85eb6223459b0b13d161c14cbb2bb6ffd65b52d6e0c79c` |
| context | context_unchanged | Will Silver (XAGUSD) hit (HIGH) $58 Week of October 19 2026? [market=5789172; condition=0xe65a2b45d5d2fcd572977d38a2644112f8aa9f7a30fea45060a8b29a3bd20af9] | Yes=0.695, No=0.305 |  | True | `52bfc22428eb3d0450ae01b72eae4490d34aebc9f3fba8cdff1ce548045614c4` |
| context | context_unchanged | Will Silver (XAGUSD) hit (LOW) $55 Week of October 19 2026? [market=5789175; condition=0x62e85c51ec8134a74a30f6f7dd5d80c614a9cfcd25ace229dc4d2ace32f1e6f7] | Yes=0.32, No=0.68 |  | True | `8be97bc4194f6b8fadf1bafbbb53d7e62ffbbfe30992f1a575b268c7d7e5a5c3` |
| context | context_unchanged | Will Silver (XAGUSD) hit (LOW) $54 Week of October 19 2026? [market=5789176; condition=0xf0851c295c97fce250ec9bbdc0a89ce71474135f47ad52ee2c00b131353b5dcc] | Yes=0.155, No=0.845 |  | True | `d0d0709140b51502e89652ef20d64d3bef1fd6018e6d26d065b23c5d77004081` |
| context | context_unchanged | Will Silver (XAGUSD) hit (LOW) $53 Week of October 19 2026? [market=5789177; condition=0x9b8f9e34a5a02844ab0852e943b2ca31ee752de887797d0293472c871ea6ff91] | Yes=0.085, No=0.915 |  | True | `d520de71e549aee49044fe9f8f7b59a854cb768f0a9120a777c306c8a07399ac` |
| context | context_unchanged | Will Silver (XAGUSD) hit (LOW) $52 Week of October 19 2026? [market=5789178; condition=0xb0616666024de6b965b98a162fadc00cfa6e3e906413e7733c67c7bba538b9c4] | Yes=0.0445, No=0.9555 |  | True | `994a0d1e907fa55403f7c254f919c1e0686d12d372401166c6764cef9da77a24` |
| context | context_unchanged | Will Silver (XAGUSD) hit (LOW) $51 Week of October 19 2026? [market=5789179; condition=0xfaf73cd11911f4f4dc476a8de24f7f838897bc2537f693851df984b6e255d439] | Yes=0.021, No=0.979 |  | True | `83883c5a288e9758e645ca97b6ad81b763cc6accb672b565605f11497090ea47` |
| context | context_unchanged | Will Silver (XAGUSD) hit (LOW) $50 Week of October 19 2026? [market=5789180; condition=0x7631447be5fc7cfa97d7788a3ce7de87341c84520e0dd5eb66b2efcf8c365b7b] | Yes=0.012, No=0.988 |  | True | `acdc0fc1ee1a6c53da164fd17fba836e23c7241ded2bc76c6097a37acc39684b` |

### TX-30 House Election Margin of Victory
Group basis: `exact_gamma_event_id`; event ID: `834872`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 244 | changed | Will the Democratic Party candidate win the 2026 TX-30 House election by 60%-65%? [market=3523717; condition=0x9ff25bde3e1e05a3582ff324c207b3d2feb0ad0ec29f53bbdebeadc199149131] | Yes=0.205, No=0.795 | best_ask | True | `78233e5563d498c64cc32f12fdb27f82a18ae9f0bbc416970b41decb2c4ef7ea` |
| context | context_unchanged | Will the Democratic Party candidate win the 2026 TX-30 House election by 55%-60%? [market=3523718; condition=0xbb3b060bf3e30b0560f0f66463ff6218037f9c37c539fbb59515c1096d931cd5] | Yes=0.2045, No=0.7955 |  | True | `22294ed7d5eac14edf5b55eb389cb67e9ac76c4008a06793a557b1e5300bec76` |

### MLB: AL Platinum Glove Winner
Group basis: `exact_gamma_event_id`; event ID: `311458`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 245 | changed | Will Ceddanne Rafaela win the 2026 AL Platinum Glove award? [market=1735322; condition=0x21dda4d02de51165d5b41014ae30c292a19a2da5ca825ace681b4bfeb180a301] | Yes=0.2, No=0.8 | spread | True | `d622e38376dc60005c51a466e2a1af953d3696920c90a40866f58d069b226902` |

## Batch 37 (15 markets)

### NASCAR Cup Series: 2026 Champion
Group basis: `exact_gamma_event_id`; event ID: `741506`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 246 | changed | Will Denny Hamlin win the 2026 NASCAR Cup Series championship? [market=3075616; condition=0x12d6bae00a0fa8b679a261d51a05b5484128bfbfa086615c0bf1cbf03a9f4c84] | Yes=0.23, No=0.77 | best_ask | True | `28b5bbe1ed022ebdc983218be9071910032522374c4781d00453d36409c863c3` |
| context | context_unchanged | Will Kyle Larson win the 2026 NASCAR Cup Series championship? [market=3075610; condition=0xd8e4484971dc78f997f3ecb75c41f942f2b2f0d2f12ecc827770f42ade8a7c85] | Yes=0.2855, No=0.7145 |  | True | `d8d2eef76a47fc5c395229925d6e51a3cc785916966e9c92f40a49113f352a5e` |
| context | context_unchanged | Will Ryan Blaney win the 2026 NASCAR Cup Series championship? [market=3075617; condition=0x53babf41ccfb7ed84c61105b67bf7d9c256b3658137993a09c2ecaa000280f5f] | Yes=0.12, No=0.88 |  | True | `ed7d2fdff69364e1dcd37b293da6d51a0f469ad99f8d956370898b761f583726` |
| context | context_unchanged | Will Chase Briscoe win the 2026 NASCAR Cup Series championship? [market=3075620; condition=0x319e74fa793b5291d437145b41684408ba55cb5402329f0433e1f8276858c1a0] | Yes=0.1465, No=0.8535 |  | True | `44b4f04a319c9d9fc09cccd98e2ceb952b86611755b624b33b8e23a0ba1e0808` |
| context | context_unchanged | Will Christopher Bell win the 2026 NASCAR Cup Series championship? [market=3075621; condition=0x3302282655ccbae08ba0679faa05ab228a4f255a2fbf901f0ce2772353791ba8] | Yes=0.19, No=0.81 |  | True | `c3745c9152a70526604f01992248f5a5575626872723e57297b0da9de3d144df` |
| context | context_unchanged | Will Joey Logano win the 2026 NASCAR Cup Series championship? [market=3075623; condition=0x9a267fe47abc3f323a18b331f860c1a92a880e000ab8fe0c9af168e216a32df5] | Yes=0.076, No=0.924 |  | True | `c3481fbfdc70cead878fa78c50558ed3a89642b81d21b8a8229186900fd1ee31` |
| context | context_unchanged | Will Bubba Wallace win the 2026 NASCAR Cup Series championship? [market=3075624; condition=0x682cc6b63bfed13147bb6812cd113580a3c4cf017df5ee3f711c1fe699d6bdc2] | Yes=0.0135, No=0.9865 |  | True | `b9bb0aab75613394c742db7b550d80896e56409e1d26a16ac12190f642059a32` |
| context | context_unchanged | Will Tyler Reddick win the 2026 NASCAR Cup Series championship? [market=3075632; condition=0xb0da73520022a9717c98a4cdcf6879cd500fbfb06df12c4c3f04561cc147be8b] | Yes=0.0285, No=0.9715 |  | True | `755a6efb5f4e660ed695ab746115bb7c9dc1a00d1aa8d39d499b2d4580beefe9` |

### Israeli Legislative Election Winner
Group basis: `exact_gamma_event_id`; event ID: `425728`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 249 | changed | Will Likud win the most seats in the 2026 Israeli legislative election? [market=2100981; condition=0xf77fa3e63014f1f76ea4433dac66b3860493ed7f1a9fee3dfbef9104d7f1eee3] | Yes=0.265, No=0.735 | best_ask | True | `a579811bf7217750d79f7d9fdf63eb2576ef4b4d2b45b11bfd08b9f1747f347e` |
| context | context_unchanged | Will Together win the most seats in the 2026 Israeli legislative election? [market=2100982; condition=0x4e9cff8a3aeac036225fedcc98af9b0d55284b3f430b599e7f61b059c1e177af] | Yes=0.0035, No=0.9965 |  | True | `23de8eee0e2cb36e87eb97517845aee49eb528102c9ea03c7ae87dd2c97dc11e` |
| context | context_unchanged | Will Yashar win the most seats in the 2026 Israeli legislative election? [market=2100984; condition=0xd05da9807740aa0f5bc9e9232daabe87a21e5012c19e283abf414f1c1651118b] | Yes=0.735, No=0.265 |  | True | `1b9064956ae8a3a6fc37e53da0d99eb7c96302e58a69f78ff16a9d0a2b1ed879` |

### What will Tesla, Inc. (TSLA) hit Week of October 19 2026?
Group basis: `exact_gamma_event_id`; event ID: `1202022`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 250 | changed | Will Tesla, Inc. (TSLA) hit (HIGH) $397.50 Week of October 19 2026? [market=5788788; condition=0xcebdfa2ea4c6ba83db86f2c4e9a06096299ec87daaf8e3510efa391ef3109a75] | Yes=0.31, No=0.69 | best_bid | True | `ebb2c516d415a351344edde101d4b7334e4783bc8df0ed87a2eefac405eb5c75` |

### Next Fable Model (5.2+) released by...?
Group basis: `exact_gamma_event_id`; event ID: `956789`. Only observed snapshot rows are included; context grouping does not establish proposition equivalence.

| Rank | Status | Market identity | Outcome prices | Changed | Semantic context | Criteria proof |
|---:|---|---|---|---|---|---|
| 252 | changed | Next Fable Model (5.2+) released by October 24, 2026? [market=5205159; condition=0x27181038a8cf9e075296846162b8f0dc247344162613407e3f0f9a313485d839] | Yes=0.535, No=0.465 | best_ask | True | `cf262224ccda13c56e030acbd9bc4e1928a50f0faaa670f4e33a2149fbbb4634` |
| context | context_unchanged | Next Fable Model (5.2+) released by October 31, 2026? [market=4178411; condition=0x611494bf2b6433b40b485671beff12d0de8cda57bfe625072e251811a145935f] | Yes=0.771, No=0.229 |  | True | `b78b5ca0afbafc19a7b51faa3dae46db7fe8290982757ae8d8d23ac03219a9d9` |
| context | context_unchanged | Next Fable Model (5.2+) released by December 31, 2026? [market=4178412; condition=0x7b5dbe811fe6465a5a4fe7529ba45fa0c78d62e1cf7c9e60ccc96ae0f5898d4c] | Yes=0.979, No=0.021 |  | True | `8297de512323382f610c93c8ddfad828d6ca1291735bf6289b68869a67cdebed` |
