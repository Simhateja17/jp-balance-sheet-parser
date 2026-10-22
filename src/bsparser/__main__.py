import json
import sys

from bsparser.output import write_outputs


def main(argv) -> int:
    if len(argv) != 2:
        print("usage: python -m bsparser <pdf> <out_dir>", file=sys.stderr)
        return 2
    json_path, csv_path = write_outputs(argv[0], argv[1])
    out = json.loads(json_path.read_text(encoding="utf-8"))
    print(f"status: {out['status']}  issues: {len(out['issues'])}  "
          f"checks: {len(out['checks'])}  records: {len(out['records'])}")
    print(f"wrote {json_path} and {csv_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
