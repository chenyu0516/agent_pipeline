#!/bin/bash
# Self-test: creates a fake project as its own git repository in a temporary directory and drives it through every
# mechanism with the tools from this checkout. Prints ALL STEPS RAN on success. Usage: scripts/selftest.sh
set -u
SRC="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
export AGENT_PIPELINE_ROOT="$SRC"
export AGENT_PIPELINE_GLOBAL_LOG="$TMP/REJECTED-global.md"
PY="uv run --quiet --project $SRC python $SRC/scripts"
step() { echo; echo "=== $*"; }
expect_fail() { if "$@"; then echo "!! EXPECTED FAILURE BUT SUCCEEDED: $*"; exit 1; else echo "(refused as expected)"; fi; }

step "1 init project as its own repo"
$PY/doc.py init vol-regime --template quant-model --title "Volatility regime filter" --at "$TMP"
cd "$TMP/vol-regime"
git config user.name tester; git config user.email t@example.com
ls -a . docs .pipeline
$PY/ref_checker.py .

step "2 project boundary: code commits are free-form, design commits are not"
echo "print('hi')" > src/run.py
git add src/run.py && git commit -q -m "add a script" && echo "free-form code commit ok"
git add -A
expect_fail git commit -q -m "add project"
expect_fail git commit -q -m "vol-regime/- INIT: project created"
$PY/commit.py --all "vol-regime/- INIT: project created" && echo ok
$PY/state.py check .

step "3 step 2a writes §problem; ownership refused for 2b"
cat > "$TMP/problem.md" <<'EOF'
## Problem
<!-- section: §problem | owner: 2a -->
Daily equity returns show volatility clustering that a constant-variance forecast ignores. We do not know whether a latent regime variable improves next-day variance forecasts over a plain autoregressive baseline. The goal is a filter whose one-day variance forecast beats that baseline out of sample.

**Choices made.** Horizon: daily, delegated at intake; picked daily because the data file lists daily bars only.
EOF
$PY/doc.py put . §problem --from "$TMP/problem.md"
expect_fail $PY/commit.py --all "vol-regime/2b PASS: wrote problem"
$PY/state.py step . 2a done --inputs seed.md
$PY/commit.py --all "vol-regime/2a PASS a1: problem framed" && echo ok

step "4 intake review on seed.md"
$PY/review.py new . --step 2a·in --kind intake --input seed.md
uv run --quiet --project "$SRC" python - docs/reviews/2a-in1.md <<'EOF'
import sys, yaml
p=sys.argv[1]; t=open(p).read(); end=t.find("\n---",3); fm=yaml.safe_load(t[3:end]); body=t[end+4:]
fm["items"]=[{"id":"Q1","severity":"framing","choice":"conditional mean or full distribution?","why_it_matters":"filter vs density","options":["mean","distribution"],"answer":"mean"},
             {"id":"Q2","severity":"detail","choice":"daily or intraday?","why_it_matters":"data plan","options":["daily","intraday"],"answer":"delegate"}]
open(p,"w").write("---\n"+yaml.safe_dump(fm,sort_keys=False,allow_unicode=True)+"---"+body)
EOF
$PY/review.py commit docs/reviews/2a-in1.md
tail -3 docs/inputs/seed.md

step "5 step 2c: notation, assumptions, formal with objects and links"
cat > "$TMP/notation.md" <<'EOF'
### Notation
<!-- section: §model.notation | owner: 2c -->

#### Daily return
<!-- object: S1 | kind: symbol -->
$r_t$, the close-to-close log return on day $t$.

#### Conditional volatility
<!-- object: S2 | kind: symbol -->
$\sigma_t$, the standard deviation of $r_t$ given information through $t-1$.
EOF
cat > "$TMP/assumptions.md" <<'EOF'
### Assumptions
<!-- section: §model.assumptions | owner: 2c -->

#### Gaussian noise
<!-- object: A1 | kind: assumption | tag: standard -->
Given [conditional volatility](#conditional-volatility), the [daily return](#daily-return) is $r_t = \sigma_t \varepsilon_t$ with $\varepsilon_t \sim N(0,1)$.

#### Volatility persistence
<!-- object: A2 | kind: assumption | tag: own -->
The autocorrelation of [conditional volatility](#conditional-volatility) at lag one exceeds $0.9$.
EOF
cat > "$TMP/formal.md" <<'EOF'
### Formal model
<!-- section: §model.formal | owner: 2c -->
Under [Gaussian noise](#gaussian-noise) and [volatility persistence](#volatility-persistence), log variance follows
$$\log \sigma_t^2 = \mu + \phi (\log \sigma_{t-1}^2 - \mu) + \eta_t. \tag{1}$$
The objective is the one-day-ahead forecast of $\sigma_{t+1}^2$.
EOF
$PY/doc.py put . §model.notation --from "$TMP/notation.md"
$PY/doc.py put . §model.assumptions --from "$TMP/assumptions.md"
$PY/doc.py put . §model.formal --from "$TMP/formal.md"
$PY/ref_checker.py .
$PY/state.py step . 2c done --inputs §problem scribble.md
$PY/commit.py --all "vol-regime/2c PASS a1: model formalized" && echo ok

step "6 bare id and banned phrase are hard failures"
cat > "$TMP/bad.md" <<'EOF'
### Derivation
<!-- section: §model.derivation | owner: 2d -->
By A1 the filter gain is constant. Previously we used a different gain.
EOF
$PY/doc.py put . §model.derivation --from "$TMP/bad.md"
expect_fail $PY/ref_checker.py . --quiet
git checkout -q -- docs && $PY/doc.py index . >/dev/null

step "7 step 2d derivation with a named result"
cat > "$TMP/deriv.md" <<'EOF'
### Derivation
<!-- section: §model.derivation | owner: 2d -->
1. By [Gaussian noise](#gaussian-noise), $\log r_t^2 = \log \sigma_t^2 + \log \varepsilon_t^2$, a linear observation of the log variance.
2. By [volatility persistence](#volatility-persistence), $\phi > 0.9$ in (1), so the state is slowly varying and a linear filter applies.

#### Steady-state gain
<!-- object: R1 | kind: result -->
The Kalman gain of the filter on (1) converges to a constant $K^\ast$ that depends only on $\phi$ and the noise variances.
EOF
$PY/doc.py put . §model.derivation --from "$TMP/deriv.md"
$PY/state.py step . 2d done --inputs §model.notation §model.assumptions §model.formal
$PY/commit.py --all "vol-regime/2d PASS a1: derivation written" && echo ok

step "8 human edit of an assumption stales 2d"
sed -i '' 's/exceeds \$0.9\$/exceeds $0.8$/' docs/DESIGN.md
$PY/commit.py --all "vol-regime/2c HUMAN: loosened persistence threshold" && echo ok
$PY/state.py show . | grep -A2 "^  2d:"
$PY/doc.py version .

step "9 review at 2f: draft, edit, commit -> pending; countered proposal logged"
$PY/review.py new . --step 2f --by idea-reviewer
R=docs/reviews/2f-r1.md
uv run --quiet --project "$SRC" python - "$R" <<'EOF'
import sys, yaml
p = sys.argv[1]; t = open(p).read(); end = t.find("\n---", 3); fm = yaml.safe_load(t[3:end]); body = t[end+4:]
fm["verdict"] = "revise"; fm["route_to"] = "2c"
fm["items"] = [
  {"id":"I1","object":"A2","section":"§model.assumptions","source":"idea-reviewer","finding":"threshold has no source",
   "proposal":"cite a paper","disposition":"counter","required":"keep own tag and add a prediction with a measurable threshold","logged":None,"status":"open","addressed_at":None,"quote":None},
  {"id":"I2","object":"R1","section":"§model.derivation","source":"idea-reviewer","finding":"gain depends on unstated noise variance",
   "proposal":"add the noise variance as a symbol","disposition":"accept","required":"add the noise variance as a symbol","logged":None,"status":"open","addressed_at":None,"quote":None},
]
open(p,"w").write("---\n"+yaml.safe_dump(fm,sort_keys=False,allow_unicode=True)+"---"+body+"\n### Edits by tester\n\nI1: a citation is not needed for an own assumption; test it instead.\n")
EOF
$PY/review.py commit "$R"
grep -E "^R1" docs/REJECTED.md

step "10 HUMAN edit off-route while review pending is refused"
sed -i '' 's/Daily equity returns show/Daily stock returns show/' docs/DESIGN.md
expect_fail $PY/commit.py --all "vol-regime/2a HUMAN: wording"
git reset -q && git checkout -q -- docs .pipeline

step "11 routed 2c reruns; verify and apply"
cat > "$TMP/notation2.md" <<'EOF'
### Notation
<!-- section: §model.notation | owner: 2c -->

#### Daily return
<!-- object: S1 | kind: symbol -->
$r_t$, the close-to-close log return on day $t$.

#### Conditional volatility
<!-- object: S2 | kind: symbol -->
$\sigma_t$, the standard deviation of $r_t$ given information through $t-1$.

#### Observation noise scale
<!-- object: S3 | kind: symbol -->
$\tau^2$, the variance of $\log \varepsilon_t^2$.
EOF
$PY/doc.py put . §model.notation --from "$TMP/notation2.md"
$PY/commit.py --all "vol-regime/2c PASS a2 2f-r1: added noise scale symbol" && echo ok
$PY/review.py verify "$R" --set I1 addressed "The autocorrelation of conditional volatility at lag one exceeds 0.8" --set I2 addressed "tau^2, the variance of log eps^2"
$PY/review.py apply "$R"
$PY/doc.py get . §status | tail -1

step "12 split §model; links rewritten; resolver by id, name, anchor"
$PY/doc.py split . §model
$PY/commit.py --all "vol-regime/- SPLIT: model to model.md" && echo ok
head -3 docs/model.md
$PY/doc.py resolve . A2 | grep -E "^(id|name|file):"
$PY/doc.py resolve . "volatility persistence" | grep -E "^(id|anchor):"
$PY/ref_checker.py .

step "13 rename by hand; hook rewrites link anchors and texts"
sed -i '' 's/#### Volatility persistence/#### Slow volatility decay/' docs/model.md
$PY/commit.py --all "vol-regime/2c HUMAN: renamed persistence assumption" && echo ok
grep -ci "slow volatility decay" docs/model.md docs/DESIGN.md

step "14 export with registry"
$PY/doc.py export .
grep -n "## Registry" docs/export/vol-regime-full.md
grep -n "stub:" docs/export/vol-regime-full.md || echo "no stubs in export (good)"

step "15 rejection log: add, span check, promote to a temp global log, revive"
$PY/review.py log add . --target "§model.formal" --proposal "model sigma_t as a GARCH one one process instead of a state space" --why "tried before, failed its prediction"
$PY/commit.py --all "vol-regime/- REJECT-LOG: garch rejected" && echo ok
cat > "$TMP/formal_bad.md" <<'EOF'
### Formal model
<!-- section: §model.formal | owner: 2c -->
We model sigma_t as a GARCH one one process instead of a state space model.
EOF
$PY/doc.py put . §model.formal --from "$TMP/formal_bad.md"
expect_fail $PY/ref_checker.py . --quiet
git checkout -q -- docs && $PY/doc.py index . >/dev/null
$PY/review.py log promote . R1
$PY/review.py log revive . R2 --why "revisit with realized variance"
$PY/commit.py --all "vol-regime/- REJECT-LOG: R2 revived" && echo ok
$PY/review.py log show . --global | tail -2

step "16 consistency and rebuild"
$PY/state.py check .
$PY/state.py rebuild .
git log --oneline | head -20
echo; echo "ALL STEPS RAN in $TMP/vol-regime"
