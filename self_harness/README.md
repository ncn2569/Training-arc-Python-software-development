# Self-Harness — thiết kế và flow hiện tại

`optimize` dùng **một task cho cả feedback và quyết định cập nhật** để giảm chi
phí prototype; `overnight` dùng cố định suite ba task nguồn để quan sát rộng hơn.
Validation là lệnh so sánh thủ công riêng, không tham gia promotion. README mô tả code hiện tại;
`artifacts/state.json` cho biết active version thực tế; `MEMORY.md` có lịch sử cũ.
Khi đổi flow, reward hoặc cách lưu kết quả, cập nhật README tương ứng.

Đọc theo câu hỏi đang cần trả lời:

| Cần hiểu gì? | Đọc ở đâu? |
| --- | --- |
| Chạy thử hoặc treo đêm | [Lệnh chạy](#2-lệnh-chạy) |
| Task, baseline, active, candidate, round khác nhau thế nào? | [Concepts](#3-concepts) |
| Một optimize thực hiện những bước nào? | [Flow code](#4-flow-code-hiện-tại) |
| Vì sao promote/reject và reward tính thế nào? | [Reward](#5-reward-và-lý-do-chọn-công-thức) |
| Judge dựa vào bằng chứng gì? | [Judge/evidence](#6-judge-và-evidence) |
| Code và folders nằm ở đâu? | [Bản đồ code](#7-folders-và-code) |
| Mở file nào để quan sát? | [Kết quả](#8-quan-sát-kết-quả-không-tạo-nhiều-side-files) |
| Bao nhiêu calls, khi nào dừng, lỗi thì sao? | [Vận hành](#9-chi-phí-dừng-và-vận-hành) |
| Muốn thay experiment thì sửa đâu? | [Cách cập nhật](#10-cách-cập-nhật-hệ-thống) |

## 1. Experiment đang làm gì?

Thử xem LLM có thể đọc kết quả thực thi, đề xuất cải tiến prompt và làm coding
agent hiệu quả hơn hay không. Không train/fine-tune model weights.

Tuner được thay `system_prompt`, descriptions của tools và parameters. Tên,
types, required fields, handlers và `SAFETY_PREFIX` cố định không được thay.
`hypothesis` giải thích đề xuất, không tham gia reward hay agent instructions.

Mục tiêu là reward gồm quality, efficiency tokens/turns/time và trừ penalty
reward-hacking có bằng chứng từ judge.
Quality có trọng số lớn nhất nhưng không phải hard gate: giảm quality vẫn có
thể thắng nếu tiết kiệm đủ bù. Prompt cần cải thiện cách làm chung, tránh nhúng
đáp án hoặc tên files của task vào global prompt.

Một task/một rollout là lựa chọn tiết kiệm cho `optimize`. `overnight` đổi scope
thành ba task nguồn, vẫn không phải validation/test độc lập. Nó không chứng minh
generalization và không loại bỏ sampling noise/overfitting. Có thể
kiểm tra task khác bằng `bench` khi cần, không bắt buộc trả chi phí đó mỗi run.
Execution isolation để cho giai đoạn thiết kế sau; workspace riêng hiện chưa
là host sandbox.

## 2. Lệnh chạy

Chạy từ `D:\Inter-K`, dùng venv và `.env` ở root.

Xem plan, không gọi API, tạo artifacts hay thay state:

~~~powershell
.\venv\Scripts\python.exe -m self_harness.cli optimize --dry-run
~~~

Thử một round trên task đơn giản:

~~~powershell
.\venv\Scripts\python.exe -u -m self_harness.cli optimize --task self_harness/tasks/telemetry_window_repair.yaml --max-rounds 1 --patience 1 --task-turns 20 --task-timeout 600
~~~

Không truyền `--task` thì mặc định cũng là `telemetry_window_repair`.
Optimize chỉ nhận một task; không còn `--train-task`, `--val-task`, `--test-task`.

So active với update ngay trước nó trên ba held-out validation tasks. Lệnh chạy hai
version mới trên cùng task suite, không gọi tuner và không promote:

~~~powershell
.\venv\Scripts\python.exe -u -m self_harness.cli validate --candidate active
~~~

`--reference parent` là mặc định. Muốn so với baseline gốc thay vì parent:

~~~powershell
.\venv\Scripts\python.exe -u -m self_harness.cli validate --candidate active --reference v000
~~~

Thử một validation task rẻ hơn:

~~~powershell
.\venv\Scripts\python.exe -u -m self_harness.cli validate --candidate active --task self_harness/tasks/heldout/val/habit_tracker.yaml --task-turns 20 --task-timeout 600
~~~

Mặc định validation dùng `inventory_dashboard`, `habit_tracker` và `fullstack_notes`.
Mỗi task tốn hai rollout, một cho reference và một cho candidate. Report ghi raw
metrics của cả hai và delta quality/penalty/reward, tokens/turns/time để thấy saving.

Treo đêm trên ba task nguồn `telemetry_window_repair`, `expense_dashboard` và
`fullstack_todo` (không gồm render hay heldout), đồng thời mirror console ra log
timestamp:

~~~powershell
.\venv\Scripts\python.exe -u -m self_harness.scripts.overnight --max-rounds 3 --patience 2 --task-turns 12 --task-timeout 600
~~~

Giữ terminal mở; launcher không phải scheduler/background service. Thêm
`--dry-run` để xem plan không tạo log. Có thể truyền một hoặc nhiều `--task` từ
ba task này nếu chỉ muốn thử subset; CLI `overnight` dùng cùng optimizer.
Caps 12 turns/600s ở lệnh trên là lựa chọn thử tiết kiệm, không đổi defaults
40 turns/900s của CLI. Một rollout chạm cap vẫn được judge để lấy partial-quality
feedback, nhưng không được báo là passed.

### Calibrate reward delta trên bảy task train

Khi cần quan sát nhiều reward delta trước khi chọn `--min-reward-gain`, dùng
launcher calibration. Nó chạy đúng bảy task source/train: telemetry window repair,
expense dashboard, fullstack todo, fullstack incident command center, feature-flag
rollout repair, inventory reservation repair và audit-log normalizer. Không dùng
bất kỳ YAML held-out nào.

~~~powershell
.\venv\Scripts\python.exe -u -m self_harness.scripts.overnight_calibration --task-turns 80 --task-timeout 600
~~~

Mặc định launcher truyền `--max-rounds 8 --patience 8 --min-reward-gain 0`,
`--control-rollouts 2`. Mọi run dùng model route/fallback cấu hình ở gateway để
ưu tiên availability; route thực tế vẫn được lưu trong audit để đọc khi diễn giải
delta nhỏ. Tổng cộng là 11 suite × 7 task (baseline + 2 controls
+ 8 candidate) trước các launcher restart; dùng `--control-rollouts 0` nếu chi
phí đêm nay quan trọng hơn đo sampling drift.
Runtime retry provider ở **cùng turn** và giữ workspace/context; nếu toàn bộ
calibration process vẫn exit lỗi (ví dụ baseline không lấy được), launcher thử
lại run mới tối đa hai lần. Truyền `--restart-attempts 0` để tắt lớp retry run
này, hoặc override các flags optimizer bình thường. Khi hoàn thành, cùng folder
với `report.md` có `reward-delta-calibration.md`: raw delta từng round, raw
quality/cost delta, cùng hai same-config control deltas để thấy sampling drift,
median/p75 observed delta và chỉ dẫn không tự coi chúng là sampling noise. Script
không tự thay `min_reward_gain`.

Xem report mới nhất, kể cả khi run đang chạy:

~~~powershell
.\venv\Scripts\python.exe -m self_harness.cli report
~~~

Nếu process cũ đang chạy flow train/val/test, Ctrl+C ở terminal đó trước khi chạy
lại. Process đã load code không tự chuyển sang flow mới khi sửa file.

## 3. Concepts

| Concept | Ý nghĩa |
| --- | --- |
| Task | YAML gồm instruction, seed, giới hạn, rubric và declared artifacts |
| Seed / fixture | Files ban đầu được copy vào workspace mới |
| Workspace | Files agent tạo/sửa trong một rollout |
| Turn | Một agent model response; có thể chứa nhiều tool calls |
| Tool call | Thao tác read/write/edit/terminal/search/load skill, không phải một LLM call |
| Trajectory | Assistant/tool events, usage, timing, errors và provider reasoning nếu có |
| Rollout | Một lần agent làm task |
| Suite / bench | Chạy một config trên các task rồi judge; optimize có một task, overnight có ba task nguồn, calibrate có bảy task source/train |
| Config | System prompt, tool declarations và metadata |
| Version | Config lâu dài dạng `vNNN.json` |
| v000 | Snapshot prompt/tools gốc; không bắt buộc bench v000 mỗi run |
| Active | Version đang được chọn, pointer trong state |
| Baseline result | Kết quả active lúc bắt đầu run; mốc chi phí cố định trong run đó |
| Incumbent / previous | Kết quả active đang dùng để so candidate; đổi sau promotion |
| Candidate | Config tuner đề xuất; chưa được promote |
| Round | Một tuner proposal → một candidate bench → promote/reject |
| Run | Một baseline bench và các rounds, không có final test tự động |
| Evidence | Quan sát cụ thể hỗ trợ xác minh requirement/finding |
| Q / R | Quality score và reward |

Baseline result và incumbent ban đầu là cùng một kết quả. Sau promotion,
incumbent đổi nhưng baseline result vẫn giữ nguyên để reward không đổi thước đo.

`candidate-r001` là tên tạm trong round 1. Nếu promote, state cấp version kế tiếp,
ví dụ `v003`; không suy version từ số round. Manifest vẫn giữ tên candidate đã
thực thi; `run.json → rounds[].promoted_version` ghi mapping.

## 4. Flow code hiện tại

~~~text
Load task scope + limits + active config
  ↓
Chạy active trên mọi task trong scope → judge Q → baseline result cố định
  ↓
Mỗi round:
  Tuner đọc active config + incumbent feedback + lịch sử thử
    → đề xuất candidate
    → chạy candidate trên CÙNG scope, workspace mới cho từng task
    → judge Q → reward chuẩn hoá theo baseline result
    → so candidate reward với incumbent reward
    → promote hoặc reject
  ↓
Dừng theo max_rounds hoặc patience → checkpoint report hoàn thành
~~~

### Khởi tạo

`cli.main()` parse flags. `optimize` gọi `tasks.load_optimization_tasks()` để nạp
đúng một YAML; `overnight` gọi `load_overnight_tasks()` để nạp ba task nguồn
(hoặc subset được truyền); `calibrate` gọi `load_calibration_tasks()` để nạp sáu
task source/train cố định (hoặc subset của bảy task đó).
`optimize()` lấy minimum của CLI caps và task YAML limits.
`ensure_baseline()` tạo v000 nếu chưa có, lấy prompt/skill index/tools từ `src/`.
Nếu v000 đã có thì không snapshot lại. `active_config()` lấy config theo state.

Optimizer bench **active lúc bắt đầu run đúng một lần**. Nếu đang active v005,
baseline của run này là kết quả v005, không chạy thêm v000.
Mốc chi phí này được giữ cố định cho tất cả candidate trong run.

### Bên trong một bench

1. Tạo `workspace/<suite-id>/<task-id>/`, copy seed hoặc bắt đầu rỗng.
2. `runtime.run_agent()` gửi fixed safety + config prompt/tools + task instruction.
3. Agent gọi model, chạy tools, thêm tool results vào context rồi tiếp tục.
4. Response không có tool calls kết thúc agent với `completed`.
5. Judge đọc task/rubric, factual tool events, final claims và inspect workspace.
6. Thu quality/evidence. Provider error không reset workspace hay agent context:
   runtime retry cùng model request của turn đó tối đa ba lần. Failed request,
   fallback backoff và retry delay được ghi audit riêng nhưng bị trừ khỏi agent
   `wall_time`; chỉ work thực tế của agent được reward. Nếu cạn retry thì bench
   lỗi, không judge hay ghi reward metrics. Judge lỗi thì rejudge tối đa một lần
   trên cùng output, không chạy agent lại.
7. Ghi một suite manifest; optimizer bổ sung reward vào cùng manifest.

Agent có thể dừng với `timeout`, `max_turns` hoặc `model_error`.
`completed` chỉ là vòng lặp kết thúc bình thường; judge mới đánh giá yêu cầu.

### Round và quyết định cập nhật

Tuner đọc config active, incumbent summary/evidence/review trajectory và tối đa
sáu thử nghiệm gần nhất. Tuner trả JSON gồm `hypothesis`, replacement prompt và
optional descriptions. Code validate, deepcopy active và merge thay đổi hợp lệ.

Candidate chỉ được chạy **một lần**. Kết quả đó vừa vào history để tuner học ở
round sau, vừa vào `decide()` để quyết định cập nhật:

~~~python
accepted = (
    candidate_evaluation_valid
    and incumbent_evaluation_valid
    and candidate_reward - incumbent_reward > min_reward_gain
)
~~~

Hai reward phải dùng cùng baseline/config reward. Validity là kiểm tra phép đo
hợp lệ, không phải hard gate bắt quality hoặc pass count phải tăng.

- Promote: lưu version mới, đổi active pointer, reuse candidate result làm
  incumbent cho round sau; reset patience về 0.
- Reject: giữ active và incumbent, tăng patience; giữ candidate feedback trong history.
- Round error: lưu lỗi và tăng patience.

Không chạy lại incumbent mỗi round, không có val/test hoặc final rerun.
`max-rounds=3` thử tối đa ba proposals. `patience=2` dừng khi hai round liên tiếp
reject/error. Baseline judge không hợp lệ thì dừng sớm, giữ report/audit.

### Ví dụ để phân biệt baseline và incumbent

Các số sau là giả định để giải thích, không phải kết quả run thực tế:

| Bước | Reward đo được | So với | Kết quả |
| --- | ---: | --- | --- |
| Active đầu run là v000 | 0.760 | Chính nó | Giữ làm cost baseline và incumbent ban đầu |
| Round 1: candidate-r001 | 0.790 | Incumbent v000: 0.760 | Promote thành v001 |
| Round 2: candidate-r002 | 0.780 | Incumbent v001: 0.790 | Reject dù cao hơn v000 |
| Round 3: candidate-r003 | 0.805 | Incumbent v001: 0.790 | Promote thành v002 |

Reference costs vẫn là kết quả v000 đầu run ở cả ba rounds. Round 2 bị reject
không làm mất v001 và không chạy lại v001. Tuner round 3 nhận active v001 cùng
lịch sử feedback của candidates trước, kể cả candidate bị reject.
Run kế tiếp bắt đầu từ v002 nếu bạn không activate version khác; nó đo một
baseline mới bằng v002. Lịch sử tuner chỉ tồn tại trong run hiện tại, không tự
đọc lại tất cả runs cũ hoặc MEMORY.md.

## 5. Reward và lý do chọn công thức

~~~text
E_cost = baseline_cost / (baseline_cost + candidate_cost)

R = 0.50 Q + 0.25 E_tokens + 0.15 E_turns + 0.10 E_wall_time
    - 0.25 P_reward_hacking
~~~

`reward.score_suite()` match task bằng ID. Baseline cost đến từ active ban đầu
của run, giữ cố định sau promotion. Baseline tự so với chính nó có E=0.5.

| Candidate cost | E |
| --- | ---: |
| Bằng baseline | 0.5 |
| Một nửa baseline | khoảng 0.667 |
| Gấp đôi baseline | khoảng 0.333 |

Ít chi phí hơn → E cao hơn, có giới hạn. Baseline cost bằng 0 dùng floor `1e-9`.
Report vẫn hiện raw tokens/turns/time để quan sát mức tiết kiệm thực tế.

Đây là công thức cộng: quality vẫn có trọng số lớn nhất (0.50), nhưng efficiency
có giá trị độc lập, kể cả khi Q thấp. Nó diễn tả rõ tradeoff prototype đang thử;
chưa có experiment chứng minh các trọng số này là tối ưu.

Baseline có `R = 0.50Q + 0.25`, vì ba efficiency đều bằng 0.5. Ví dụ
Q=0.95 → R=0.725. Candidate Q=0.92, tokens=50%, turns=75%, time=90% baseline
có R khoảng 0.765 và có thể thắng.

Q lấy từ judge score, kể cả partial work. `P_reward_hacking` nằm trong [0, 1]
và chỉ khác 0 khi judge đưa finding có evidence cho hành vi thao túng đánh giá
(ví dụ sửa evaluation assets, bypass check rồi khai là đã chạy, hoặc bịa artifact).
Bug bình thường, partial work hay test agent tự viết yếu không phải hacking.
Penalty bị nhân 0.25 rồi trừ ở cuối reward. Pass/status là diagnostics, không phải
gate. Agent costs vào reward;
judge/tuner usage được ghi riêng như overhead.
Do baseline có thể khác giữa runs, không so reward của hai runs như cùng thước đo.

## 6. Judge và evidence

| Consumer | Harness gửi gì |
| --- | --- |
| Agent | Fixed safety, config/tools, task instruction, seed và tool results |
| Judge | Task/rubric, status/final claims, factual tool events và workspace inspection |
| Tuner | Active config, observed metrics, Judge feedback/trajectory và history; công thức tổng quát không có trọng số |
| Local audit | Exact config/task contracts/judge instructions, raw trajectories/verdicts/usage |

Agent không nhận rubric/reward feedback trong initial context. Judge review không
gửi provider reasoning, assistant narrative hoặc usage. Tuner dùng review đầy đủ
hơn để hiểu execution friction. Đây là data routing, chưa là host access control.

Tuner chỉ thấy công thức với hệ số ký hiệu. Không gửi `reward_config`, weighted
reward totals hoặc reward breakdown qua summary, từng task hay history; giữ các số
này trong local audit/report. Tuner vẫn thấy Q, tokens/turns/time và evidence để học
từ kết quả thực thi. Từ round thứ hai, history còn có unified diff bị giới hạn của
prompt, mọi tool-description change, quyết định promote/reject, cùng raw delta
quality/pass/tokens/turns/time so với incumbent đã thử; không có reward value hay
weight nào trong payload đó. Tuner thấy finding/penalty của judge để tránh lặp lại
hành vi bị phát hiện, nhưng không thấy penalty weight.

Raw trajectories giữ events/reasoning provider có trả. Review che content/edit
source bodies, giữ tool intent/metadata/exit status và stdout/stderr tails tối đa
1.500 ký tự. Không chủ động ghi credentials vào metadata. Image bytes không được
copy vào tool audit; ảnh vẫn đi vào model context khi đọc.

Evidence cần được hiểu đúng:

- Write thành công: đã ghi bytes, chưa chứng minh implementation đúng.
- Read thành công: đọc được file/ảnh; dimensions chỉ là metadata.
- Terminal exit 0: command báo thành công, chưa chứng minh check hữu ích.
- Source inspection: bằng chứng code có logic/consistency được yêu cầu.
- Test result: bằng chứng của command/test cụ thể; test agent tự viết chưa là kiểm tra độc lập.
- Image inspection: bằng chứng nội dung nhìn thấy khi rubric yêu cầu visual.
- Final answer: claim cần đối chiếu, không phải proof.

Verdict judge:

~~~json
{
  "passed": true,
  "score": 0.9,
  "reason": "short explanation",
  "evidence": [
    {"requirement": "behavior", "observation": "observed fact", "reference": "file/location", "verified": true}
  ],
  "reward_hacking": {"penalty": 0.0, "findings": []}
}
~~~

Judge chấm Q và một penalty reward-hacking độc lập. Penalty chỉ áp dụng cho hành vi
đã xác minh nhằm thao túng đánh giá, không suy đoán ý định hay phạt bug/partial work
thông thường. Nonzero penalty bắt buộc có findings kèm evidence. Code validate type,
finite range [0,1] và schema; độ đúng/coverage của evidence vẫn dựa vào Judge inspection.

Tuner được yêu cầu cải thiện reusable workflow, không nhúng task IDs/đáp án/file
inventories/rubric markers, không hướng agent thao túng judge hoặc metrics.
Runtime giữ fixed safety prefix bên ngoài prompt tuner được sửa.

Judge có tối đa 24 model inspection rounds mỗi attempt; một round có thể dùng
nhiều tools. Text reader hỗ trợ offset sau 30.000 ký tự; image limit 10 MB;
test timeout tối đa 120s, chạy trong temporary copy. Judge có thể đọc supporting
files ngoài declared artifacts. Tests/copy không phải host isolation.

`passed = raw judge passed AND score >= pass_score AND agent status == completed`.
Passed là diagnostic; Q mới tham gia reward.

## 7. Folders và code

~~~text
D:/Inter-K/
  main.py, src/                 agent gốc
  sessions/, workspace/         history/output của agent gốc
  venv/, .env                   environment/gateway dùng chung
  Self-Harness-main/            source tham khảo; CLI này không gọi
  self_harness/
    README.md, MEMORY.md        flow hiện tại / lịch sử bàn giao
    tasks/                      đề YAML; mặc định telemetry_window_repair
      heldout/val/, test/       tasks còn giữ để bench thủ công; không tự chạy
    fixtures/                   seed input
    configs/                    hiện chưa được implementation dùng
    scripts/                    routes, health check, overnight launcher
    artifacts/                  state, versions, run summaries, detailed audits
    workspace/                  files thực tế mỗi task rollout
~~~

Không nhầm workspace root agent với `self_harness/workspace/`. Runtime harness
triển khai loop/handlers riêng, lấy prompt/tool contract gốc. Promotion không tự
đổi `main.py`, chưa chứng minh cải thiện chuyển sang agent gốc có memory/compaction.

| Module | Hàm chính / trách nhiệm |
| --- | --- |
| [cli.py](cli.py) | `main()`: flags, dry-run, dispatch |
| [tasks.py](tasks.py) | `load_task()`, `load_optimization_tasks()`, `load_tasks()`: YAML và task selection |
| [optimizer.py](optimizer.py) | `optimize()`, `decide()`, `_render_report()`: baseline, rounds, promotion, checkpoints |
| [bench.py](bench.py) | `run_bench()`, `_aggregate()`: workspace → agent → judge → manifest |
| [runtime.py](runtime.py) | `run_agent()`, `execute_tool()`, `prepare_workspace()`: execution và metrics |
| [judge.py](judge.py) | `judge_task()`, `_validate_verdict()`, `JUDGE_INSTRUCTIONS`: Q/evidence |
| [reward.py](reward.py) | `score_suite()`, `REWARD_CONFIG`: normalization và scalar reward |
| [tuner.py](tuner.py) | `propose_candidate()`, `_apply_descriptions()`, `TUNER_INSTRUCTIONS`: proposal/validation |
| [config.py](config.py) | `ensure_baseline()`, `active_config()`, `save_promoted_version()`: paths/state/versions |
| [trajectory.py](trajectory.py) | `review_trajectory()`: compact judge/tuner review |
| [models.py](models.py) | `call_model()`, `extract_json()`: completions, routing, usage |
| [scripts/model_routes.py](scripts/model_routes.py) | primary/fallback order |
| [scripts/overnight.py](scripts/overnight.py) | launcher và console log |

Đọc theo `cli → optimizer → bench → runtime/judge → reward → decide`, rồi tuner/config.

Task mẫu tại [telemetry_window_repair.yaml](tasks/telemetry_window_repair.yaml):

| Field YAML | Vai trò |
| --- | --- |
| `id` | Tên task/workspace, chỉ chữ/số/underscore/hyphen |
| `prompt` | Yêu cầu gửi cho agent; phải nêu deliverables và giới hạn công việc |
| `seed_dir` | Đường dẫn seed tính từ self_harness; seed được copy mỗi rollout |
| `max_turns`, `timeout_seconds` | Giới hạn task, còn được giảm bởi CLI caps |
| `judge.rubric` | Tiêu chí gửi cho judge, giữ cố định khi so candidates |
| `judge.pass_score` | Ngưỡng diagnostic passed; không phải ngưỡng promotion |
| `judge.artifacts` | Deliverables khai báo, mỗi record có path/mode text hoặc image/render |

Task mặc định được chọn ở `tasks.DEFAULT_BENCH_TASK_PATH`. Folders heldout/val/test
chỉ là nơi chứa YAML còn giữ lại; tên folder không kích hoạt split evaluation.

`tasks/heldout/test/` hiện có thêm tám challenge tasks chạy thủ công qua
`bench --task`: ledger reconciliation, clinic booking boundaries, offline sync
conflicts, safe archive paths, release dependency cycles, incident alert
deduplication, emergency-triage UI và JSONL redaction CLI. Sáu task đầu có
seeded stdlib tests cố ý fail; chúng đo khả năng quan sát lỗi, sửa đúng nguyên
nhân và rerun bounded test. Chúng không mô phỏng provider failure: provider
retry được runtime xử lý ngay tại model turn lỗi, không reset rollout.

## 8. Quan sát kết quả, không tạo nhiều side files

~~~text
artifacts/state.json
artifacts/versions/vNNN.json
artifacts/optimization-runs/run-<timestamp>-<id>/
  report.md                    bắt đầu xem tại đây
  run.json                     plan/proposals/summaries/audit links
  judge.json                   verdict/evidence/penalty/inspection của mỗi bench
  tuner.json                   hypothesis/proposal/usage/decision của mỗi round
artifacts/validation-runs/validation-<timestamp>-<id>/
  report.md, run.json           so sánh held-out reference/candidate, không promotion
artifacts/suites/suite-<id>/manifest.json
workspace/suite-<id>/<task-id>/  output duy nhất của task
artifacts/logs/overnight-*.log  chỉ launcher tạo
~~~

Report có baseline metrics. Mỗi round có một dòng metrics thực tế của candidate và
một dòng delta riêng so với incumbent đã dùng để quyết định. Q/reward là chênh
điểm; token/turn/time là phần trăm thay đổi (dương nghĩa là candidate đắt hơn).
Không dồn metric và delta vào cùng một ô.
`RUNNING` đổi thành `PROMOTED`, `REJECTED` hoặc `ERROR` khi round xong. Stage cập
nhật theo checkpoints, không theo từng turn.

`run.json` chỉ có một file mỗi run, được cập nhật dần:

| Key | Nội dung |
| --- | --- |
| `mode`, `active_version`, `baseline_version`, `stage` | Scope (`single-task`/`overnight-suite`), selected version, run-start version và tiến trình |
| `plan.tasks`, `reward_config` | Task/source/effective limits, rounds/patience, route và formula |
| `suites.baseline`, `suites.candidate-NNN` | Summary và manifest path, không copy trajectories |
| `rounds[]` | Parent, merged config/hypothesis, tuner usage, candidate_summary, reward_gain, decision/reason/promoted_version |
| `selected_summary`, `selected_manifest_path`, `stop_reason` | Kết quả active cuối và lý do dừng |
| `error` | Baseline evaluation lỗi nếu có |

Đọc trực tiếp hai model quan trọng:

- `judge.json → suites.baseline.tasks[0].judge`: `reason`, `score`, tối đa năm
  evidence records, inspection count và tối đa tám mẫu
  tool/target ngắn gọn, model/usage. Candidate tương ứng nằm trong
  `suites["candidate-001"]`. Có previous attempts khi rejudge lỗi.
- `tuner.json → rounds[0]`: `hypothesis`, raw JSON `proposal`, usage/model/retries,
  decision/reason/gain và promoted version nếu có. Round lỗi cũng được ghi tại đây.

Hai files được tạo ngay đầu run và cập nhật qua checkpoints; không tăng LLM calls.
Judge file chỉ lưu căn cứ ra quyết định đã thu gọn, không thêm chain-of-thought
hay toàn bộ output inspection. Muốn audit chi tiết một nghi vấn cụ thể thì lần
theo manifest của suite; đó là nơi duy nhất giữ raw inspection/trajectory.
`run.json.rounds[]` giữ decision gốc; `tuner.json` lấy decision từ cùng round state
qua `_tuner_audit()`. Không có hai nơi tự quyết định promote/reject. `proposal`
là JSON tuner trả; `run.json.rounds[].config` là config đầy đủ đã merge/validate,
có tools được kế thừa mà tuner không cần trả lại toàn bộ.
Muốn xem agent trajectory/source: run.json → suite manifest → task.workspace_path.
Manifest giữ exact config/task/judge instructions, raw trajectory, judge
inspection/verdict/usage và reward components. Trong một task, rejudge history chỉ
thêm previous failed attempts; không chép final judge lại vào attempt history.

Run mới có **bốn files: report.md, run.json, judge.json, tuner.json**; không tạo per-round audit folders,
plan/history/error side files hoặc `.self_harness_result.json` trong output.
Tuner raw JSON proposal nằm trong tuner.json; merged runnable config vẫn ở run.json.
Judge verdict cũng giữ trong manifest để audit task đầy đủ; agent trajectory không
copy vào hai files mới. Output chỉ giữ một bản tại workspace.
Không xóa/migrate historical runs; report train/val/test cũ
vẫn phản ánh code cũ. Không có auto-prune hoặc automatic resume.

## 9. Chi phí, dừng và vận hành

Với N rounds, `optimize` tối đa **1 + N task rollouts**; `overnight` tối đa
**3 × (1 + N)** rollouts. Provider failure retry cùng model request tối đa ba
lần trong rollout, không reset task. Một round có một candidate rollout cho mỗi
task trong scope, mỗi rollout có agent và judge, cộng một call tuner. Call count
không cố định:
agent tối đa task turns, judge tối đa
24 calls/attempt; rejudge tối đa một lần nếu lỗi. API retries/fallback có thể thêm
request attempts. Không gọi model để test cuối run.
`validate` dùng đúng hai rollout cho mỗi held-out task đã chọn.

| Flag | Default | Ý nghĩa |
| --- | ---: | --- |
| `--task` | optimize: telemetry_window_repair | Optimize: đúng một YAML; overnight: optional subset của ba task nguồn |
| `--max-rounds` | 3 | Tối đa số candidate proposals |
| `--patience` | 2 | Reject/error liên tiếp trước khi dừng |
| `--min-reward-gain` | 0 | Candidate gain phải lớn hơn mức này; ties reject |
| `--task-timeout` | 900 | Cap thời gian agent task, check giữa turns |
| `--task-turns` | 40 | Cap agent model turns |
| `--dry-run` | false | In plan không execute |

Effective limit là minimum CLI/YAML. In-flight calls có thể vượt time budget;
judge có budget riêng. Không có hard deadline cho toàn đêm.
Provider usage ưu tiên; fallback LiteLLM token estimate rồi serialized char estimate.
Không phải mọi failed API attempt đều có usage để tính đầy đủ chi phí.

Model route chung cho agent/judge/tuner, primary rồi fallback sau error; chỉnh tại
`scripts/model_routes.py`. `.env` cần API_KEY/API_BASE/MODEL; không copy vào audits.
Health check gọi API thật: `python -m self_harness.scripts.test_litellm_models`.
Trong `MODEL_FALLBACKS`, entry đầu là primary; các entry sau là fallback theo thứ
tự. Hiện route chỉ giữ DeepSeek vì health check ngày 2026-09-14 xác nhận nó hoạt
động, còn Qwen không có account và kCode không có worker. Nếu danh sách rỗng thì
dùng MODEL trong .env. Mỗi `call_model()` bắt đầu thử lại từ primary, không pin
một model cho toàn run. Adapter đặt timeout 120s mỗi request; judge/tuner audits
và agent trajectory ghi actual model đã dùng.

Baseline evaluation lỗi → dừng. Candidate evaluation lỗi → không promote,
tiêu patience. Q thấp/P cao nhưng evaluation hợp lệ vẫn tham gia reward.
`complete` nghĩa orchestration đã xong, không phải mọi task passed.
Ctrl+C giữ completed benches/checkpoints và promotions đã làm. Gọi lại tạo run mới.

Rollback/switch active:

~~~powershell
.\venv\Scripts\python.exe -m self_harness.cli activate v000
~~~

Lệnh đổi pointer, không xóa versions/audits hoặc generated files. `next_version`
cấp ID khi promote, không phải số rounds. V000 chỉ snapshot config, không snapshot
runtime/judge/reward; sửa evaluator cần đo lại bằng run mới.

Bench thủ công task khác, không tuner/promotion và không normalized reward:

~~~powershell
.\venv\Scripts\python.exe -m self_harness.cli bench --version active --task self_harness/tasks/heldout/val/habit_tracker.yaml
~~~

`bench --task` có thể lặp để kiểm tra nhiều task khi cần. Các task dashboard,
fullstack và image vẫn có thể chọn qua YAML; optimize chỉ chạy task được chọn.
Source-only score đo code coherence/logic, chưa thay bằng chứng app chạy đúng.

## 10. Cách cập nhật hệ thống

Giữ các trách nhiệm rõ ràng: optimizer điều phối/chọn, runtime thực thi, judge
chấm, reward tính điểm và tuner đề xuất. Chỉnh trực tiếp module có trách nhiệm
đó; chưa cần thêm framework, config layer hoặc một optimizer riêng cho overnight.

| Muốn đổi | Nơi sửa |
| --- | --- |
| Task đang chạy | CLI `--task`; đổi mặc định tại `tasks.DEFAULT_BENCH_TASK_PATH` |
| Suite calibration bảy task | `tasks.CALIBRATION_TASK_NAMES`; launcher `scripts/overnight_calibration.py` |
| Instruction/rubric/seed/task limits | YAML của task |
| Caps/rounds/patience cho một run | CLI flags; defaults tại `cli._optimization_options()` và `optimizer.optimize()` |
| Prompt/evidence/penalty philosophy của judge | `judge.JUDGE_INSTRUCTIONS` |
| Verdict JSON schema | `judge._validate_verdict()` và phần kết quả trong `judge_task()` |
| Tuner đề xuất cải tiến thế nào | `tuner.TUNER_INSTRUCTIONS` và `propose_candidate()` |
| Text nào tuner được phép sửa | `tuner._schema_view()` và `_apply_descriptions()` |
| Reward weights và penalty default | `reward.REWARD_CONFIG`; CLI/optimizer/scoring cùng lấy penalty default ở đây |
| Normalization/công thức | `reward.score_suite()`; cập nhật công thức mô tả cho tuner và README |
| Promotion/stop conditions | `optimizer.decide()` và vòng round trong `optimize()` |
| Run report và model audit shape | `optimizer._render_report()`, `_tuner_audit()`, `bench()`/`checkpoint()` bên trong optimize |
| Agent tools/usage/loop | `runtime.py`; tổng hợp metrics tại `bench._aggregate()` |
| Detailed suite manifest | `bench.run_bench()` |
| Model primary/fallback | `scripts/model_routes.MODEL_FALLBACKS` |
| State/version paths và fixed safety | `config.py` |

Khi sửa một hành vi, cập nhật phần README tương ứng trong cùng thay đổi và dùng
`--dry-run` kiểm tra lệnh/plan nếu thay CLI/task selection. Sửa evaluator hoặc
task contract thì chạy run mới để đo baseline lại. Không sửa số đo/audit cũ để
khiến chúng giống flow mới. Nếu thêm field vào audit, ghi rõ nơi người đọc tìm nó.

Mỗi run tiếp tục có bốn files dễ quan sát; trajectories và output vẫn ở suite
manifest/workspace. Chỉ thêm file/module khi có nhu cầu cụ thể mà các nơi này
không xử lý rõ ràng được. README giữ current flow; MEMORY giữ lịch sử, không
được dùng các version/state lịch sử như trạng thái active hiện tại.
