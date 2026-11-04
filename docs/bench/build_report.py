"""Build the HW7 report PDF from the numbers in docs/bench/evidence/.

    python -I docs/bench/build_report.py      # writes docs/bench/HW7-Rebbi-benchmark.pdf

Every number in the tables comes from docs/bench/evidence/<benchmark>/results.csv; the prose quotes
the same files. Edit TEAM below, then rebuild.
"""

from __future__ import annotations

import csv
import statistics
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (KeepTogether, PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"
OUT = HERE / "HW7-Rebbi-benchmark.pdf"
COMMIT = "99848ca2c633a341ebaf34449ca256e35ae52a51"
REPO = "https://github.com/eglismella/rebbi"

# Names under the title, contributions in section 8; the grading agent identifies the team from this list.
TEAM = [
    ("Eglis Mella", "designed the benchmark (claim, arms, cases), built the runner and the auto-borrow change, ran "
     "all 115 runs, and wrote the analysis and this report."),
    ("Pietro Bertone", "independent check of the results: recomputed every number in the results tables from the raw "
     "results files, and traced sampled runs from their logs to those files."),
    ("Nitya Maddineni", "independent check of the ground truth: re-derived the answer key for the hardest repository "
     "(llm 0.12) from its source code and compared it with ours."),
]
NAMES = ", ".join(name for name, _ in TEAM)


def rows(bench: str) -> list[dict]:
    with open(EVIDENCE / bench / "results.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def cell(rs: list[dict], case: str | None, arm: str, kinds=("ordinary", "hard"), split: str | None = None) -> list[dict]:
    return [r for r in rs if r["arm"] == arm and (r["case"] == case if case else r["kind"] in kinds)
            and (split is None or r["split"] == split)]


def ok(rs: list[dict]) -> str:
    return f"{sum(r['success'] == 'True' for r in rs)}/{len(rs)}" if rs else "-"


def med(rs: list[dict], key: str) -> str:
    return f"{round(statistics.median(int(r[key]) for r in rs)):,}" if rs else "-"


MAIN, RETEST = rows("main"), rows("retest-autoborrow")
HINT, NOHINT, SCARCE = rows("stress-hint15k"), rows("stress-nohint"), rows("stress-scarce")
CASES = ["sqlite-utils-3.38", "csvs-to-sqlite-1.3.1", "sqlite-utils-3.30", "db-to-sqlite-1.5", "llm-0.12",
         "no-lender-room"]
SPLIT = {r["case"]: (r["kind"], r["split"]) for r in MAIN}

base = getSampleStyleSheet()
BODY = ParagraphStyle("body", parent=base["Normal"], fontName="Helvetica", fontSize=9.4, leading=12.4,
                      spaceAfter=5, alignment=TA_LEFT)
SMALL = ParagraphStyle("small", parent=BODY, fontSize=8.2, leading=10.2, spaceAfter=2)
CELL = ParagraphStyle("cell", parent=BODY, fontSize=8, leading=9.6, spaceAfter=0)
H1 = ParagraphStyle("h1", parent=base["Title"], fontName="Helvetica-Bold", fontSize=15, leading=19, spaceAfter=4,
                    alignment=TA_LEFT)
H2 = ParagraphStyle("h2", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=11, leading=14,
                    spaceBefore=8, spaceAfter=4, textColor=colors.HexColor("#1f3a5f"))


def p(text: str, style=BODY) -> Paragraph:
    return Paragraph(text, style)


def link(path: str, label: str | None = None, tree: bool = False) -> str:
    return f'<link href="{REPO}/{"tree" if tree else "blob"}/{COMMIT}/{path}" color="#1f5fbf">{label or path}</link>'


def bullets(items: list[str]) -> list[Paragraph]:
    return [Paragraph(i, BODY, bulletText="•") for i in items]


def table(data: list[list], widths: list[float], bold_rows: tuple[int, ...] = ()) -> Table:
    body = [[c if isinstance(c, Paragraph) else Paragraph(str(c), CELL) for c in row] for row in data]
    t = Table(body, colWidths=[w * inch for w in widths], repeatRows=1)
    style = [("FONT", (0, 0), (-1, -1), "Helvetica", 8),
             ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eef6")),
             ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor("#1f3a5f")),
             ("LINEBELOW", (0, 1), (-1, -1), 0.25, colors.HexColor("#c8d0da")),
             ("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]
    for i in bold_rows:
        style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f4f6f9")))
    t.setStyle(TableStyle(style))
    return t


def b(text: str) -> Paragraph:
    return Paragraph(f"<b>{text}</b>", CELL)


story = [
    p("Rebbi: does lending spare token budget help agents finish their jobs?", H1),
    p(f"Team: {NAMES}<br/>"
      f"HW7: Benchmark Your Agentic System. Repository {link('', 'github.com/eglismella/rebbi', tree=True)}, "
      f"commit {COMMIT[:7]} (branch hw7-benchmark). All runs on Nov 3, 2026.", SMALL),
    Spacer(1, 4),

    p("1. Claim", H2),
    p("Rebbi is infrastructure for a fleet of agents: an agent that is about to run out of token budget mid-job "
      "borrows spare budget from an idle agent over MCP, and gives back what it does not use. "
      "<b>Claim:</b> when an agent's own budget is too small for its job, Rebbi lets it borrow, so the job "
      "finishes and passes an independent check, and no lender drops below the reserve it published."),
    p("<b>Main metric:</b> success rate per arm. A run succeeds only if (1) the <b>verifier</b> passes: "
      "11 checks of the report against a hand-checked answer key for that repository; the agent saying "
      "\"done\" does not count; (2) the <b>ledger check</b> passes: no tokens created or lost, every loan closed; "
      "(3) no loan left its lender below its <b>reserve</b>. These rules were written down before any run "
      f"({link('docs/bench/PLAN.md')}). <b>Costs per run:</b> auditor tokens, whole-fleet tokens (lenders "
      "included), seconds, and the dollar cost the Claude CLI reports for the auditor."),

    p("2. Setup", H2),
    p("<b>Job.</b> dep-audit-v1: audit the Python dependencies of a repository at a pinned commit and write a "
      "7-section report with a JSON appendix (runtime and optional dependencies, which files import each, "
      "unused and undeclared imports, unpinned versions). The auditor can only Read, Grep and Glob."),
    p("<b>Fleet.</b> auditor-01 (Claude Sonnet 5.5) has 7,000 tokens: enough for about one model call, while the "
      "passing audits here took 11,600 to 43,700. analyst-07 (Claude Haiku 5.5) has 180,000 with a reserve of 80,000 "
      "and 20,000 of declared demand, so 80,000 is lendable; writer-03 has nothing above its reserve. Budgets are "
      "enforced per model call: a call goes ahead only if the balance covers its input."),
    table([
        [b("Arm"), b("What happens")],
        ["baseline", "Rebbi off. The auditor has only its own 7,000 tokens. It fails by construction; it shows the problem."],
        ["upfront", "Rebbi off. Before the job, the owner moves the job's expected cost (the hint the auditor is "
                    "also given, 60,000) from the lender with the most spare room to the auditor. A manager who "
                    "knew the cost in advance. Tokens are not given back. <b>This is the fair, simpler baseline.</b>"],
        ["rebbi", "Rebbi on. The auditor can ask Rebbi for budget over MCP; unspent tokens go back when the job ends."],
    ], [0.8, 6.2]),
    Spacer(1, 3),
    p("Every arm has the same job, repositories, prompt and fleet total. The only differences are the ones in "
      "the table: the upfront arm's owner moves tokens before the job, and the rebbi arm adds Rebbi's tools to "
      "the auditor and has the lenders publish their reserves (which costs them tokens, counted in fleet tokens)."),
    table([
        [b("Case"), b("Kind"), b("Split"), b("Why it is here")],
        ["sqlite-utils-3.38", "ordinary", "tuning", "The HW6 demo job: 7 files, 5 optional undeclared imports"],
        ["csvs-to-sqlite-1.3.1", "ordinary", "tuning", "Smallest; py-lru-cache is imported as lru"],
        ["sqlite-utils-3.30", "ordinary", "fresh", "Older release; click-default-group-wheel imported under another name"],
        ["db-to-sqlite-1.5", "ordinary", "fresh", "Simplest dependency picture"],
        ["llm-0.12", "hard", "fresh", "Largest (15 files, 11 dependencies); three name traps; pip is run, never imported"],
        ["no-lender-room", "failure", "tuning", "sqlite-utils-3.38 with analyst-07 at exactly reserve + demand: nobody can lend"],
    ], [1.35, 0.65, 0.55, 4.45]),
    Spacer(1, 3),
    p("<b>Case selection.</b> Picked before any run: small Python packages by one author whose setup.py lists "
      "dependencies literally (the only format our answer-key script reads); the first five that worked were "
      "kept. datasette 0.65.1 was dropped because it vendors another library, which makes its answer key "
      "ambiguous. Each key was generated from the source and checked by hand. <b>Tuning</b> cases may be "
      "studied to design a change; <b>fresh</b> cases are held back to check it. <b>Repeats:</b> 3 runs per case "
      "and arm, arms interleaved, because the model is random. In all: 105 benchmark runs plus 10 diagnostic "
      "runs; the auditor's reported cost was $3.09 for the 105."),
    p("<b>To repeat:</b> <font face='Courier'>pip install -e .[test]; python -m rebbi fetch-target --all; "
      "python -m rebbi.bench --label main</font> (needs a Claude login in .env). Each stress setting's exact "
      f"command is in its folder under {link('docs/bench/evidence', 'docs/bench/evidence', tree=True)}."),
]

# 3. Main results
main_rows = [[b("Case"), b("baseline"), b("upfront"), b("rebbi"), b("upfront tokens*"), b("rebbi tokens*")]]
for c in CASES:
    main_rows.append([c] + [ok(cell(MAIN, c, a)) for a in ("baseline", "upfront", "rebbi")]
                     + [med(cell(MAIN, c, "upfront"), "auditor_tokens"), med(cell(MAIN, c, "rebbi"), "auditor_tokens")])
main_rows.append([b("ordinary + hard")] + [b(ok(cell(MAIN, None, a))) for a in ("baseline", "upfront", "rebbi")]
                 + [b(med(cell(MAIN, None, "upfront"), "auditor_tokens")), b(med(cell(MAIN, None, "rebbi"), "auditor_tokens"))])
story += [
    p("3. Results before any change (main run, 51 runs)", H2),
    KeepTogether([table(main_rows, [1.6, 0.8, 0.8, 0.8, 1.4, 1.4], bold_rows=(len(main_rows) - 1,)),
                  p("Success counts (runs that met all three checks out of 3, or 15 pooled). *Median auditor tokens. "
                    f"Source: {link('docs/bench/evidence/main/results.csv')}.", SMALL)]),
    p("Safety held: no reserve was broken and every ledger check passed in all 51 runs; in no-lender-room Rebbi "
      "answered CANNOT_MOVE and the job stopped cleanly. But <b>Rebbi passed only 4 of 15</b> while upfront passed "
      "15 of 15. In every failed rebbi run the auditor started the audit before asking Rebbi: its first call used "
      "about 5,500 of its 7,000 tokens, the low-budget warning arrived after that call, and the next call, the one "
      "that would have carried the request, needed more input than was left, so it was refused. Every rebbi run "
      "that asked first passed."),

    p("4. The limit, the change, and the retest", H2),
    p("<b>Diagnosis.</b> In the four saved HW6 demo runs the auditor asked first. One thing differed: to add repositories we never "
      "measured, the cost hint changed from \"past runs ... <i>on this commit</i> used up to 60,000 tokens\" to "
      "\"past runs of dep-audit-v1 used up to 60,000 tokens\". A check on sqlite-utils-3.38 (tuning), 10 runs "
      "alternating the two wordings: HW6 wording asked first 5/5 and passed 5/5; new wording 1/5 and 1/5 "
      f"({link('docs/bench/evidence/wording-check/results.csv', 'wording-check/results.csv')}). "
      "So Rebbi's benefit hung on whether the model chose to ask early, and a few words flip that choice."),
    p("<b>The one change: auto-borrow</b> (written into the plan before the retest). When a model call's input "
      "is more than the auditor's balance, the harness, or the gateway with an API key, asks Rebbi for a loan on "
      "the auditor's behalf before refusing the call: the rest of the expected cost, and at least enough for this "
      "call and one more of its size. All lending rules stay (most-room lender first, cap, reserves, unspent "
      f"tokens returned). Code: <font face='Courier'>top_up</font> in {link('rebbi/fleet.py')}. Prompt, budgets and "
      "cases are unchanged, including the wording that failed. It was designed from tuning-case evidence only "
      "(one passing fresh-case log was opened while diagnosing)."),
]

retest_rows = [[b("Cases"), b("rebbi before"), b("rebbi after"), b("upfront"), b("after: auditor tokens*"),
                b("after: fleet tokens*"), b("after: seconds*")]]
for label, split in (("tuning (2 repos)", "tuning"), ("fresh (3 repos)", "fresh")):
    retest_rows.append([label, ok(cell(MAIN, None, "rebbi", split=split)), ok(cell(RETEST, None, "rebbi", split=split)),
                        ok(cell(MAIN, None, "upfront", split=split)), med(cell(RETEST, None, "rebbi", split=split), "auditor_tokens"),
                        med(cell(RETEST, None, "rebbi", split=split), "fleet_tokens"),
                        med(cell(RETEST, None, "rebbi", split=split), "seconds")])
retest_rows.append(["no-lender-room", ok(cell(MAIN, "no-lender-room", "rebbi")), ok(cell(RETEST, "no-lender-room", "rebbi")),
                    ok(cell(MAIN, "no-lender-room", "upfront")), "-", "-", "-"])
retest_rows.append([b("all ordinary + hard"), b(ok(cell(MAIN, None, "rebbi"))), b(ok(cell(RETEST, None, "rebbi"))),
                    b(ok(cell(MAIN, None, "upfront"))), b(med(cell(RETEST, None, "rebbi"), "auditor_tokens")),
                    b(med(cell(RETEST, None, "rebbi"), "fleet_tokens")), b(med(cell(RETEST, None, "rebbi"), "seconds"))])
retest_rows.append(["upfront, for cost", "", "", "", med(cell(MAIN, None, "upfront"), "auditor_tokens"),
                    med(cell(MAIN, None, "upfront"), "fleet_tokens"), med(cell(MAIN, None, "upfront"), "seconds")])
story += [
    KeepTogether([p("<b>Retest</b> (rebbi arm only, since nothing else changed; every case, 3 runs each, 18 runs):"),
                  table(retest_rows, [1.45, 0.8, 0.8, 0.7, 1.2, 1.1, 0.95], bold_rows=(4,)),
                  p("*Medians. Upfront figures are from the main run. Sources: "
                    f"{link('docs/bench/evidence/retest-autoborrow/results.csv', 'retest-autoborrow/results.csv')}, "
                    f"{link('docs/bench/evidence/main/results.csv', 'main/results.csv')}.", SMALL)]),
    p("<b>What improved:</b> success went from 0/6 to 6/6 on the tuning cases and from 4/9 to 9/9 on the fresh "
      "cases, so the fix holds where it was not designed. Auto-borrow fired in 11 of 15 runs; in the other 4 the "
      "agent asked on its own. No-lender-room still fails, correctly. <b>What did not:</b> cost. Rebbi now spends "
      "about 1.5 times upfront's auditor tokens and twice its fleet tokens, and takes about twice as long. Two "
      "causes, both visible in the logs: the lenders spend about 8,700 tokens publishing their reserves, and a "
      "side effect of the change: the old low-budget warning reaches the model after auto-borrow has already "
      "lent, so the model spends one more call (about 7,700 tokens) asking for a loan it does not need. Fixing "
      "that would be a second change, so it is reported as a limit."),
]

stress_rows = [[b("Setting (tuning cases, after the change)"), b("upfront"), b("rebbi"), b("upfront tokens*"),
                b("rebbi tokens*"), b("Source")]]
for label, rs, folder in (("Wrong hint: auditor told 15,000, not 60,000", HINT, "stress-hint15k"),
                          ("No hint: told nothing about cost", NOHINT, "stress-nohint"),
                          ("Scarce lender: analyst-07 has 20,000 to spare", SCARCE, "stress-scarce")):
    stress_rows.append([label, ok(cell(rs, None, "upfront")), ok(cell(rs, None, "rebbi")),
                        med(cell(rs, None, "upfront"), "auditor_tokens"), med(cell(rs, None, "rebbi"), "auditor_tokens"),
                        p(link(f"docs/bench/evidence/{folder}/results.csv", f"{folder}"), CELL)])
story += [
    KeepTogether([p("5. Where Rebbi helps, and where it stops helping (36 runs)", H2),
                  table(stress_rows, [2.55, 0.6, 0.6, 1.0, 1.0, 1.25]),
                  p("*Median auditor tokens. One setting changed at a time; 3 runs per repo and arm.", SMALL)]),
    p("When the cost is wrong or unknown, upfront moves too little (15,000) or nothing and fails; Rebbi does not "
      "need the number, because auto-borrow asks when a call cannot be covered: 12/12 against 4/12. When spare "
      "budget is scarce, Rebbi loses: analyst-07 spent about 4,400 of its 20,000 spare tokens publishing its "
      "reserve, so Rebbi could lend only 15,636, the stale-warning call spent about 9,400 more, and the auditor "
      "ended about 2,200 tokens short on sqlite-utils-3.38 (0/3), leaving 15,636 of the lender's tokens spent on a "
      "failed job. Upfront moved all 20,000 with no overhead and passed 6/6. One upfront run took 4,527 s because "
      "a single model call took 74 minutes to return (Rebbi was off); it only widens the time range."),

    p("6. What the evidence supports, and what it does not", H2),
    *bullets([
        "<b>Supported:</b> lending gets budget-short jobs done when nobody knows the job's cost in advance "
        "(rebbi 12/12, upfront 4/12 under a wrong or missing hint), and it never broke a reserve or the ledger "
        "in 115 runs. With auto-borrow it matched upfront's success (15/15) on all five repositories, including "
        "three it was not designed on.",
        "<b>Not supported:</b> that Rebbi is the better choice when the cost is known. A manager who moves the right "
        "amount up front succeeds as often for about half the tokens and time, and wins outright when spare "
        "budget is scarce, because Rebbi's own overhead uses part of it.",
        "<b>Fragility:</b> before the change, whether Rebbi helped depended on the model choosing to ask first, and "
        "one sentence of wording moved that from 5/5 to 1/5. Auto-borrow removes that dependence for budget "
        "shortfalls only.",
        "<b>Uncertainty:</b> 3 runs per cell. Gaps like 6/6 against 4/6 could be chance at this size; 15/15 against "
        "4/15 and 12/12 against 4/12 are large. The retest and stress runs were compared with upfront numbers "
        "from earlier the same day rather than interleaved with them. The stress runs came after the change, "
        "not before as planned, and covered only the two tuning repositories.",
        "<b>Scope:</b> one job type, one auditor model, five small repositories by one author, three agents on one "
        "machine, one borrower at a time. Our answer keys, though hand-checked, could hold an error; it would hit "
        "every arm alike. Only the hardest key (llm 0.12) was re-checked by a second person. Dollar figures are the CLI's estimate for the auditor only; tokens are the main cost "
        "measure. The baseline fails by construction.",
        "<b>Unproven:</b> many borrowers competing for one lender, loans expiring mid-job, longer or different "
        "jobs, other models, and whether removing the stale warning closes the cost gap.",
    ]),

    p("7. Evidence", H2),
    p(f"Plan, fixed before the runs, with a dated log of each result and change: {link('docs/bench/PLAN.md')}. "
      f"Every run's console log, report, verifier output, summary and agent transcripts: "
      f"{link('docs/bench/evidence/README.md', 'docs/bench/evidence/')} (CLI settings and SQLite ledgers left out; "
      f"no credentials). Cases: {link('config/bench.toml')}; repositories and commits: {link('config/targets.toml')}; "
      f"answer keys: {link('specs', 'specs/', tree=True)}; runner: {link('rebbi/bench.py')}. "
      "The appendix shows two runs' logs. Two team members who did not run the benchmark checked it on their own "
      "(section 8)."),

    p("8. Team", H2),
    *[Paragraph(f"<b>{name}</b>: {what}", BODY, bulletText="•") for name, what in TEAM],
]


# Appendix: real log lines, read from the evidence files when the PDF is built, never retyped.
MONO = ParagraphStyle("mono", parent=BODY, fontName="Courier", fontSize=6.5, leading=7.7, spaceAfter=3)
BEFORE, AFTER = "20261103-171245-rebbi", "20261103-204302-rebbi"  # sqlite-utils-3.30 (fresh), rebbi arm
WIDTH, INDENT = 128, " " * 22  # a log line is "HH:MM:SS  <who, 12 wide><what>"


def keep(line: str) -> bool:
    """Leave out the lenders' chat replies and writer-03, which has no room to lend."""
    who, what = line[10:22].strip(), line[22:]
    if who == "writer-03" or (who == "harness" and what.startswith("writer-03")):
        return False
    return not (what.startswith("says: ") and who != "auditor-01")


def wrap(line: str) -> list[str]:
    """At most two printed rows per log line; anything longer is cut and ends with '...'."""
    if len(line) <= WIDTH:
        return [line]
    cut = line.rfind(" ", len(INDENT), WIDTH + 1)  # break between words where possible
    cut = cut if cut > 0 else WIDTH
    rest = INDENT + line[cut:].lstrip()
    return [line[:cut], rest if len(rest) <= WIDTH else rest[:WIDTH - 3] + "..."]


def excerpt(run: str) -> Preformatted:
    lines = (EVIDENCE / "runs" / run / "console.log").read_text(encoding="utf-8").splitlines()
    out, last = [], -1
    for i, line in enumerate(lines):
        if not keep(line):
            continue
        if i != last + 1:
            out.append("  ...")
        out += wrap(line)
        last = i
    if last != len(lines) - 1:
        out.append("  ...")
    return Preformatted("\n".join(out), MONO)


def run_link(run: str) -> str:
    return link(f"docs/bench/evidence/runs/{run}", run, tree=True)


story += [
    PageBreak(),
    p("Appendix: two runs, straight from the logs", H2),
    p("Both runs audit the same fresh repository (sqlite-utils 3.30) with Rebbi on: one from the main run, before "
      "the change, and one from the retest, after it. The PDF's build script copies these lines from each run's "
      "console.log; \"...\" marks lines left out (the lenders' chat replies, and writer-03, which has no room to "
      "lend), and very long lines are cut. Each line is time (US Eastern; run names are UTC), who, and what. Token "
      "counts are per model call.", SMALL),
    p(f"<b>A. Before the change: stopped, verifier FAIL.</b> Run {run_link(BEFORE)}.", SMALL),
    excerpt(BEFORE),
    p("The auditor started the audit without asking Rebbi. Its first call used 5,511 of its 7,000 tokens, the next "
      "needed 10,989, and the call was refused. \"used 16500 tokens\" counts that refused call's input: the request "
      "had already reached the model service when the harness stopped it.", SMALL),
    p(f"<b>B. After the change: finished, verifier PASS.</b> Run {run_link(AFTER)}.", SMALL),
    excerpt(AFTER),
    p("Same start, but auto-borrow (\"harness top-up\") asks Rebbi before refusing the call, and analyst-07 lends "
      "54,504. The auditor then asks for 21,129 more on its own, because of the stale low-budget warning (section "
      "4); that second loan is the extra cost. What is unspent goes back at the end (38,884). This is the most "
      "expensive passing run in the benchmark (43,749 auditor tokens), picked because it audits the same "
      "repository as A, not because it looks best.", SMALL),
]

doc = SimpleDocTemplate(str(OUT), pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                        topMargin=0.65 * inch, bottomMargin=0.65 * inch, title="Rebbi HW7 benchmark",
                        author=NAMES)


def footer(canvas, doc_) -> None:
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#6b7785"))
    canvas.drawString(0.75 * inch, 0.4 * inch, f"Rebbi HW7 benchmark, commit {COMMIT[:7]}")
    canvas.drawRightString(letter[0] - 0.75 * inch, 0.4 * inch, f"page {doc_.page}")


doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(f"wrote {OUT}")
