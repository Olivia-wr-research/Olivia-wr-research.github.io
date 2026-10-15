# Contributing

Useful changes improve a visible user task: source inspection, screening, data portability or metadata diagnostics. Include a small failure case and a regression test where appropriate. Do not add opaque expertise scores, inferred employment labels or private source examples.

Run `python -m unittest discover -s tests -v`. For UI changes, open the public example and verify filtering, shortlist export and decision restore. Keep the HTML report self-contained. No test should make a live API request.
