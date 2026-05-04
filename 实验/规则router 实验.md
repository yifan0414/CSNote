---
创建时间: 2026-04-28 03:00
数据集: EgoSchema
性能: 50
git commit:
---

# EgoSchema Adaptive Experiment Summary

Date: 2026-04-26  
Result file: `outputs/artifacts/egoschema_adaptive/egoschema_pred_adaptive.json`  
Format: JSONL, one prediction record per line

## Commands

Evaluation command used:

```bash
python eval/eval_multiple_choice_qa.py \
  --pred_path outputs/artifacts/egoschema_adaptive/egoschema_pred_adaptive.json
```

Reconstructed inference command, based on the current `scripts/run_eval_egoschema.sh`
defaults and this output path:

```bash
OUTPUT_DIR=outputs/artifacts/egoschema_adaptive \
OUTPUT_NAME=egoschema_pred_adaptive \
FRAME_SELECTION=adaptive \
NUM_FRAMES=100 \
TEMPERATURE=0 \
scripts/run_eval_egoschema.sh
```

Key inferred runtime settings:

| Setting | Value |
| --- | --- |
| Task | EgoSchema multiple-choice QA |
| Inference script | `run_inference_multiple_choice_qa.py` |
| Eval script | `eval/eval_multiple_choice_qa.py` |
| Frame selection requested | `adaptive` |
| Max requested frames | `100` |
| Conv mode | `multiple_choice_allvideo_v4` |
| Input structure | `image_seq` |
| Temporal aggregation | `spatial_tome_finch_dynamic_all_frms` |
| Image aspect ratio | `resize` |
| RoPE scaling factor | `2` |
| Temperature | `0` |

## Main Result

Evaluation output:

```text
EgoSchema
    Yes count: 250
    No count: 250
    Accuracy: 0.5
```

Summary:

| Metric | Value |
| --- | ---: |
| Total examples | 500 |
| Correct | 250 |
| Wrong | 250 |
| Overall accuracy | 50.00% |

## Adaptive Routing Breakdown

Although all examples requested `adaptive`, the router selected different concrete
sampling strategies per question.

| `frame_selection_used` | Count | Correct | Wrong | Accuracy |
| --- | ---: | ---: | ---: | ---: |
| `uniform` | 453 | 225 | 228 | 49.67% |
| `segment_motion` | 47 | 25 | 22 | 53.19% |

By router question type:

| `router_question_type` | Count | Correct | Wrong | Accuracy |
| --- | ---: | ---: | ---: | ---: |
| `global_temporal` | 419 | 210 | 209 | 50.12% |
| `action_local` | 47 | 25 | 22 | 53.19% |
| `default` | 30 | 12 | 18 | 40.00% |
| `counting` | 4 | 3 | 1 | 75.00% |

By frame budget:

| `num_frames_used` | Count | Correct | Wrong | Accuracy |
| --- | ---: | ---: | ---: | ---: |
| 64 | 453 | 225 | 228 | 49.67% |
| 48 | 47 | 25 | 22 | 53.19% |

Interpretation:

- `adaptive` mostly selected `uniform`, because most EgoSchema questions matched
  global or temporal keywords such as `overall`, `objective`, `purpose`,
  `sequence`, `theme`, or `throughout`.
- `segment_motion` was used only for `action_local` questions, all with a
  48-frame budget.
- In this run, `segment_motion` was slightly higher than `uniform`
  by accuracy, but the subset is small: 47 examples.

## Option Distribution

Ground-truth option distribution:

| Correct option | Count |
| --- | ---: |
| A | 101 |
| B | 108 |
| C | 91 |
| D | 83 |
| E | 117 |

Predicted option distribution:

| Predicted option | Count |
| --- | ---: |
| A | 126 |
| B | 84 |
| C | 119 |
| D | 111 |
| E | 60 |

Accuracy by ground-truth option:

| Correct option | Count | Correct | Wrong | Accuracy |
| --- | ---: | ---: | ---: | ---: |
| A | 101 | 46 | 55 | 45.54% |
| B | 108 | 48 | 60 | 44.44% |
| C | 91 | 56 | 35 | 61.54% |
| D | 83 | 57 | 26 | 68.67% |
| E | 117 | 43 | 74 | 36.75% |

Accuracy by predicted option:

| Predicted option | Count | Correct | Wrong | Accuracy |
| --- | ---: | ---: | ---: | ---: |
| A | 126 | 46 | 80 | 36.51% |
| B | 84 | 48 | 36 | 57.14% |
| C | 119 | 56 | 63 | 47.06% |
| D | 111 | 57 | 54 | 51.35% |
| E | 60 | 43 | 17 | 71.67% |

Notable pattern:

- The model predicted `E` much less often than it appeared in the ground truth
  (`60` predictions vs. `117` ground-truth examples).
- When it did predict `E`, precision was relatively high at 71.67%.

## How `segment_motion` Works

Implementation: `dataset.py`

For video files, the function is `get_segment_motion_frames`. For directories of
pre-extracted frames, the function is `get_segment_motion_frame_paths`.

The algorithm:

1. Split the whole video into `desired_num_frames` uniform time segments.
2. For each segment, load candidate frames inside that segment.
3. Convert frames to grayscale.
4. Compute mean absolute pixel difference between adjacent frames.
5. Pick the later frame from the adjacent pair with the largest local change.

So the difference is:

| Strategy | Selection rule |
| --- | --- |
| `uniform` | Pick the middle frame from each uniform segment |
| `segment_motion` | Pick the frame after the largest local pixel change in each segment |

This keeps global temporal coverage while biasing the sampled evidence toward
local action or motion. It is lightweight, but it is only based on pixel
difference, so camera motion and lighting changes can also be counted as motion.

## Router Rules Relevant To This Run

Implementation: `question_router.py`

In adaptive mode:

| Matched type | Strategy | Frame budget |
| --- | --- | ---: |
| `counting` | `uniform` | 64 |
| `global_temporal` | `uniform` | 64 |
| `action_local` | `segment_motion` | 48 |
| `static_attribute` | `single_frame` | 1 |
| `default` | `uniform` | 64 |

For this result file, the `segment_motion` examples were triggered by action
keywords. The most common trigger reasons were:

| Router reason | Count |
| --- | ---: |
| `matched action keywords: actions` | 15 |
| `matched action keywords: activities` | 7 |
| `matched action keywords: activity` | 6 |
| `matched action keywords: actions, performed` | 4 |
| `matched action keywords: action` | 3 |
| `matched action keywords: actions, perform` | 2 |

## Warnings And Issues Observed

### Generation warning

Observed warning:

```text
`do_sample` is set to `False`. However, `temperature` is set to `0.0`
```

Reason: with `TEMPERATURE=0`, the script sets `do_sample=False`, but still passes
`temperature=0.0` into `model.generate`. The generation is deterministic, and
`temperature` is ignored. This warning is harmless for the result, but it can be
cleaned up by only passing `temperature` when `temperature > 0`.

### Evaluation JSON parsing issue

Earlier error:

```text
NameError: name 'false' is not defined. Did you mean: 'False'?
```

Reason: the prediction file is JSONL and stores booleans as JSON values
`true` / `false`. Python `eval` expects `True` / `False`. The correct reader is
`json.loads`, not `eval`.

The current eval script now reads lines with `json.loads`, and the evaluation
command runs successfully.

### `pynvml` warning

Observed warning:

```text
FutureWarning: The pynvml package is deprecated. Please install nvidia-ml-py instead.
```

This comes from PyTorch CUDA initialization. It does not affect the accuracy
calculation.

## Takeaways

- Adaptive routing did not drastically change the sampling strategy for most
  EgoSchema questions: 90.6% of examples still used `uniform`.
- `segment_motion` was selected for 9.4% of examples and performed slightly
  better than `uniform` on that subset.
- The current keyword router strongly prioritizes global or temporal keywords
  before action keywords. This explains why many broad EgoSchema questions route
  to `uniform`.
- A next useful analysis would compare this adaptive run against fixed
  `uniform`, fixed `segment_motion`, and possibly a hybrid strategy using the
  same evaluation script and identical model settings.
