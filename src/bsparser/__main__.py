import argparse
import json
import sys

from bsparser.analyse import ROUNDING_CHOICES, analyse
from bsparser.output import write_outputs


def main(argv) -> int:
    parser = argparse.ArgumentParser(prog="python -m bsparser", description="Parse the balance sheet page of a PDF.")
    parser.add_argument("pdf")
    parser.add_argument("out_dir")
    parser.add_argument("--page", type=int, default=None, help="page to parse (default: the best balance sheet page)")
    parser.add_argument("--rounding", choices=ROUNDING_CHOICES, default="auto",
                        help="auto takes the cover hint; an explicit value is recorded as chosen by the user")
    args = parser.parse_args(argv)
    out = analyse(args.pdf, page=args.page, rounding=args.rounding)
    json_path, csv_path = write_outputs(args.pdf, args.out_dir, output=out)
    saved = json.loads(json_path.read_text(encoding="utf-8"))
    print(f"page: {saved['page']} of {saved['pages_total']}  status: {saved['status']}  issues: {len(saved['issues'])}  "
          f"checks: {len(saved['checks'])}  records: {len(saved['records'])}")
    print(f"rounding: {saved['rounding']} ({saved['rounding_source']}) {saved['rounding_sentence'] or saved['rounding_note']}".rstrip())
    print(f"wrote {json_path} and {csv_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
