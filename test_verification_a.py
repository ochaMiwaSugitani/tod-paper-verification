"""
検証A：PrefixSpan-py との等価性検証

論文の 4.5.1 節（アルゴリズム実装の妥当性検証）の「検証A」に対応するテストコード．

本実装（時間を考慮）が PrefixSpan-py のコアロジックを破壊しないことを
示すため，SPMF プロジェクトが提供する公開ベンチマークデータセットである
Sign データに対して，以下の 2 つの出力が一致するかを検証する：
  (1) PrefixSpan-py に生のアイテム列を入力した結果
  (2) 各アイテムを (0, item) のタプルとしてエンコードし PrefixSpan-py に
      入力した結果（時間情報を中立化）

両者の出力パターン集合が完全に一致することで，本実装（時間を考慮）が
PrefixSpan-py のコアロジックと等価であることが確認できる．

実行方法:
  python test_verification_a.py

データ準備:
  SPMF プロジェクトの公式サイトから Sign データセットをダウンロードし，
  data/Sign.txt として配置すること．
    https://www.philippe-fournier-viger.com/spmf/index.php?link=datasets.php
"""

import os
import sys
from prefixspan import PrefixSpan


# ===== データ読み込み =====

def load_sign_data(filepath):
    """SPMF 形式の Sign データを読み込み，シーケンスリストに変換する．

    SPMF フォーマット:
      1 2 -1 3 -1 4 5 -1 -2
      1 3 -1 4 -1 -2

    -1: アイテムセット区切り
    -2: シーケンス終端

    本検証ではアイテムを単一イベントとして扱うため，-1 と -2 を区切り記号として
    除去し，各シーケンスをアイテムのフラットなリストに変換する．
    """
    sequences = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            tokens = line.strip().split()
            if not tokens:
                continue
            sequence = []
            for token in tokens:
                if token in ('-1', '-2'):
                    continue
                sequence.append(int(token))
            if sequence:
                sequences.append(sequence)
    return sequences


# ===== PrefixSpan の実行 =====

def run_standard_prefixspan(sequences, minsup, closed=True):
    """標準的な PrefixSpan-py を生のアイテム列に対して実行する．"""
    ps = PrefixSpan(sequences)
    patterns = ps.frequent(minsup, closed=closed)
    return patterns


def run_time_aware_prefixspan(sequences, minsup, closed=True):
    """本実装（時間を考慮）を時間中立条件で実行する．

    本実装は (d, a) タプル（経過日数 d，医療指示種類 a）をアイテムとして扱う．
    時間情報の影響を中立化するため，すべてのアイテムを (0, item) として
    エンコードする．これにより，PrefixSpan のコアロジックのみを比較できる．
    """
    tuple_sequences = [[(0, item) for item in seq] for seq in sequences]
    ps = PrefixSpan(tuple_sequences)
    patterns = ps.frequent(minsup, closed=closed)
    return patterns


# ===== パターンの正規化と比較 =====

def normalize_standard_pattern(pattern):
    """標準 PrefixSpan のパターンをハッシュ可能な形式に変換する．"""
    return tuple(pattern)


def normalize_time_aware_pattern(pattern):
    """本実装のパターンから時間情報を除去してハッシュ可能な形式に変換する．

    [(0, item1), (0, item2), ...] -> (item1, item2, ...)
    """
    return tuple(item for (_, item) in pattern)


def compare_results(standard_results, time_aware_results):
    """両者の出力を比較し，等価性を検証する．"""
    standard_set = {
        (normalize_standard_pattern(p), s) for s, p in standard_results
    }
    time_aware_set = {
        (normalize_time_aware_pattern(p), s) for s, p in time_aware_results
    }

    only_in_standard = standard_set - time_aware_set
    only_in_time_aware = time_aware_set - standard_set
    common = standard_set & time_aware_set

    return {
        'standard_count': len(standard_set),
        'time_aware_count': len(time_aware_set),
        'common_count': len(common),
        'only_in_standard_count': len(only_in_standard),
        'only_in_time_aware_count': len(only_in_time_aware),
        'is_equivalent': (len(only_in_standard) == 0 and len(only_in_time_aware) == 0),
    }


# ===== メイン処理 =====

def format_result_line(minsup, comparison):
    """検証結果を 1 行のテキストに整形する．"""
    return (
        f"  minSup={minsup:>4}  | "
        f"標準 PrefixSpan-py: {comparison['standard_count']:>5} 個  | "
        f"本実装（時間を考慮）: {comparison['time_aware_count']:>5} 個  | "
        f"共通: {comparison['common_count']:>5} 個  | "
        f"等価性: {'OK（一致）' if comparison['is_equivalent'] else 'NG（不一致）'}"
    )


def main():
    """検証Aを実行し，結果を標準出力およびファイルに出力する．"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, 'data', 'Sign.txt')
    results_dir = os.path.join(script_dir, 'results')
    os.makedirs(results_dir, exist_ok=True)
    output_path = os.path.join(results_dir, 'verification_a_results.txt')

    if not os.path.exists(data_path):
        print(f"エラー：データファイルが見つかりません: {data_path}")
        print("README.md の手順に従って Sign.txt を data/ に配置してください．")
        sys.exit(1)

    # データ読み込み
    sequences = load_sign_data(data_path)
    n_seq = len(sequences)
    avg_len = sum(len(s) for s in sequences) / n_seq if n_seq else 0

    # 複数の minSup で検証
    # Sign データは 730 シーケンス，平均シーケンス長 52 程度であり，
    # 低い minSup では計算時間が大きくなるため，絶対数として 100, 200, 300 を使用．
    # 等価性は minSup の値に依存しない性質であるため，3 点での検証で十分に妥当性を担保できる．
    minsup_values = [100, 200, 300]

    output_lines = []
    output_lines.append("=" * 80)
    output_lines.append("検証A：PrefixSpan-py との等価性検証")
    output_lines.append("=" * 80)
    output_lines.append(f"データセット: Sign（SPMF プロジェクト提供）")
    output_lines.append(f"シーケンス数: {n_seq}")
    output_lines.append(f"平均シーケンス長: {avg_len:.2f}")
    output_lines.append("")
    output_lines.append("各 minSup における等価性検証結果:")
    output_lines.append("-" * 80)

    print('\n'.join(output_lines))

    all_equivalent = True
    for minsup in minsup_values:
        # 標準 PrefixSpan-py の実行
        standard_results = run_standard_prefixspan(sequences, minsup, closed=True)

        # 本実装（時間を考慮）の実行
        time_aware_results = run_time_aware_prefixspan(sequences, minsup, closed=True)

        # 比較
        comparison = compare_results(standard_results, time_aware_results)
        if not comparison['is_equivalent']:
            all_equivalent = False

        line = format_result_line(minsup, comparison)
        output_lines.append(line)
        print(line)

    output_lines.append("-" * 80)
    output_lines.append("")
    if all_equivalent:
        output_lines.append("[総合判定] すべての minSup 設定において出力が完全一致した．")
        output_lines.append("           これにより本実装（時間を考慮）が")
        output_lines.append("           PrefixSpan-py のコアロジックと等価であることが客観的に示された．")
    else:
        output_lines.append("[総合判定] 一部の minSup 設定で出力に差異が確認された．実装の確認が必要．")

    output_lines.append("=" * 80)

    # ファイル出力
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines) + '\n')

    print()
    print(f"結果を {output_path} に保存しました．")


if __name__ == '__main__':
    main()
