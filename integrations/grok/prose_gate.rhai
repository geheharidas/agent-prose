let meta = #{
    name: "prose-gate",
    description: "Deterministic stylometric quality gate for autonomous agent deliverables"
};

let target = if args == () || args.target == () {
    "deliverable.md"
} else {
    args.target
};

let output = sh(`agent-prose --locale en-AU ${target}`);
complete(output);
