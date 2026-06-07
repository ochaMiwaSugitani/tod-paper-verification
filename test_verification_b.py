"""
検証B：時間間隔処理の動作検証

論文の 4.5.1 節（アルゴリズム実装の妥当性検証）の「検証B」に対応するテストコード．

手作成した 5 名の患者シーケンスに対して，本実装の出力が手計算による期待値と
完全に一致することを確認する．特に，経過日数が異なるアイテム
（例：(1, '抗生剤') と (2, '抗生剤')）が正しく区別されることを検証する．

実行方法:
  python test_verification_b.py
"""

import os
from time_aware_pattern_extractor import extract_time_aware_patterns


# ===== テストデータ =====
# 論文 4.5.1 節 検証B で記述された手作成シーケンス（5 名分）．
# 各シーケンスは (経過日数, 医療指示種類) のタプルのリスト．
TEST_DATA = [
    [(0, '手術'), (1, '抗生剤'), (2, '検査')],     # 患者1
    [(0, '手術'), (1, '抗生剤')],                 # 患者2
    [(0, '手術'), (2, '抗生剤')],                 # 患者3
    [(0, '手術'), (1, '抗生剤'), (2, '検査')],     # 患者4
    [(0, '手術'), (1, '検査')],                   # 患者5
]


# ===== 期待値（手計算による導出） =====
# minSup = 3（5 名中 3 名以上）における頻出パターン．
#
# 個別アイテムの出現数:
#   (0, '手術')  : 5 名 → 頻出
#   (1, '抗生剤'): 3 名（患者1, 2, 4） → 頻出
#   (2, '抗生剤'): 1 名（患者3） → 非頻出
#   (1, '検査')  : 1 名（患者5） → 非頻出
#   (2, '検査')  : 2 名（患者1, 4） → 非頻出
#
# 順序を保ったシーケンスパターンの出現数:
#   <(0,手術)>:                              5 名 → 頻出
#   <(1,抗生剤)>:                            3 名 → 頻出
#   <(0,手術), (1,抗生剤)>:                  3 名 → 頻出
#   <(0,手術), (2,検査)>:                    2 名 → 非頻出
#   <(1,抗生剤), (2,検査)>:                  2 名 → 非頻出
#   <(0,手術), (1,抗生剤), (2,検査)>:        2 名 → 非頻出
#   <(0,手術), (2,抗生剤)>:                  1 名 → 非頻出
#   <(0,手術), (1,検査)>:                    1 名 → 非頻出
#
# クローズド頻出パターン:
#   - <(0, 手術)> はサポート 5 で出現し，同じサポートを持つ上位パターンが
#     存在しないためそのまま残る．
#   - <(1, 抗生剤)> はサポート 3 で出現するが，<(0, 手術), (1, 抗生剤)> も
#     サポート 3 で出現し，前者を包含するため，クローズド条件では
#     <(0, 手術), (1, 抗生剤)> のみが残る．

EXPECTED_PATTERNS_CLOSED = [
    (5, [(0, '手術')]),
    (3, [(0, '手術'), (1, '抗生剤')]),
]

EXPECTED_PATTERNS_ALL = [
    (5, [(0, '手術')]),
    (3, [(1, '抗生剤')]),
    (3, [(0, '手術'), (1, '抗生剤')]),
]


# ===== 比較用ヘルパー関数 =====

def patterns_to_set(patterns):
    """パターンリストをハッシュ可能な集合に変換する．"""
    return {(support, tuple(pattern)) for support, pattern in patterns}


def compare_patterns(actual, expected):
    """本実装の出力と手計算による期待値を比較する．"""
    actual_set = patterns_to_set(actual)
    expected_set = patterns_to_set(expected)
    return {
        'is_match': actual_set == expected_set,
        'only_in_actual': actual_set - expected_set,
        'only_in_expected': expected_set - actual_set,
    }


def format_pattern(pattern):
    """パターンを人間が読みやすい文字列に整形する．"""
    items = ', '.join(f"({d},{e})" for d, e in pattern)
    return f"<{items}>"


# ===== メイン処理 =====

def main():
    """検証Bを実行し，結果を標準出力およびファイルに出力する．"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(script_dir, 'results')
    os.makedirs(results_dir, exist_ok=True)
    output_path = os.path.join(results_dir, 'verification_b_results.txt')

    lines = []
    lines.append("=" * 80)
    lines.append("検証B：時間間隔処理の動作検証")
    lines.append("=" * 80)

    lines.append("テストデータ（5 名の患者シーケンス）:")
    for i, seq in enumerate(TEST_DATA, 1):
        items = ', '.join(f"({d},{e})" for d, e in seq)
        lines.append(f"  患者{i}: <{items}>")
    lines.append("")

    minsup = 3
    lines.append(f"minSup = {minsup}（5 名中 3 名以上 = 60% 以上）")
    lines.append("")

    # ---- closed = True での検証 ----
    lines.append("-" * 80)
    lines.append("[closed = True での検証]")
    lines.append("")

    actual_closed = extract_time_aware_patterns(TEST_DATA, minsup, closed=True)
    actual_closed.sort(key=lambda x: (-x[0], x[1]))

    lines.append("本実装による出力:")
    for support, pattern in actual_closed:
        lines.append(f"  サポート: {support}, パターン: {format_pattern(pattern)}")
    lines.append("")
    lines.append("手計算による期待値:")
    for support, pattern in EXPECTED_PATTERNS_CLOSED:
        lines.append(f"  サポート: {support}, パターン: {format_pattern(pattern)}")
    lines.append("")

    cmp_closed = compare_patterns(actual_closed, EXPECTED_PATTERNS_CLOSED)
    if cmp_closed['is_match']:
        lines.append("[判定] 本実装の出力は期待値と完全一致した．")
    else:
        lines.append("[判定] 出力と期待値に差異がある．")
        if cmp_closed['only_in_actual']:
            lines.append("  本実装の出力のみに含まれるパターン:")
            for support, pattern in cmp_closed['only_in_actual']:
                lines.append(f"    サポート: {support}, パターン: {format_pattern(list(pattern))}")
        if cmp_closed['only_in_expected']:
            lines.append("  期待値のみに含まれるパターン:")
            for support, pattern in cmp_closed['only_in_expected']:
                lines.append(f"    サポート: {support}, パターン: {format_pattern(list(pattern))}")
    lines.append("")

    # ---- closed = False での検証 ----
    lines.append("-" * 80)
    lines.append("[closed = False（全頻出パターン）での検証]")
    lines.append("")

    actual_all = extract_time_aware_patterns(TEST_DATA, minsup, closed=False)
    actual_all.sort(key=lambda x: (-x[0], x[1]))

    lines.append("本実装による出力:")
    for support, pattern in actual_all:
        lines.append(f"  サポート: {support}, パターン: {format_pattern(pattern)}")
    lines.append("")
    lines.append("手計算による期待値:")
    for support, pattern in EXPECTED_PATTERNS_ALL:
        lines.append(f"  サポート: {support}, パターン: {format_pattern(pattern)}")
    lines.append("")

    cmp_all = compare_patterns(actual_all, EXPECTED_PATTERNS_ALL)
    if cmp_all['is_match']:
        lines.append("[判定] 本実装の出力は期待値と完全一致した．")
    else:
        lines.append("[判定] 出力と期待値に差異がある．")
        if cmp_all['only_in_actual']:
            lines.append("  本実装の出力のみに含まれるパターン:")
            for support, pattern in cmp_all['only_in_actual']:
                lines.append(f"    サポート: {support}, パターン: {format_pattern(list(pattern))}")
        if cmp_all['only_in_expected']:
            lines.append("  期待値のみに含まれるパターン:")
            for support, pattern in cmp_all['only_in_expected']:
                lines.append(f"    サポート: {support}, パターン: {format_pattern(list(pattern))}")

    lines.append("")
    lines.append("-" * 80)
    overall = cmp_closed['is_match'] and cmp_all['is_match']
    if overall:
        lines.append("[総合判定] 時間間隔処理が手計算による期待値と一致して動作することが確認された．")
        lines.append("           特に，経過日数の異なるアイテムが正しく区別されていることが示された．")
    else:
        lines.append("[総合判定] 出力と期待値に差異があり，実装の確認が必要．")
    lines.append("=" * 80)

    text = '\n'.join(lines) + '\n'
    print(text)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)

    print(f"結果を {output_path} に保存しました．")


if __name__ == '__main__':
    main()
