from itertools import combinations

# 點數對應：將 1 視為 14 (Ace)
def get_rank_value(num):
    return 14 if num == 1 else num

def classify_5(cards):
    ranks = sorted([get_rank_value(c[0]) for c in cards], reverse=True)
    suits = [c[1] for c in cards]
    
    is_flush = (len(set(suits)) == 1)
    
    # 判斷順子（包含一般順子與 A-2-3-4-5 特殊順子）
    is_straight = False
    straight_high = 0
    
    unique_ranks = sorted(list(set(ranks)), reverse=True)
    if len(unique_ranks) == 5:
        # 一般順子：例如 14, 13, 12, 11, 10 或 9, 8, 7, 6, 5
        if ranks[0] - ranks[4] == 4:
            is_straight = True
            straight_high = ranks[0]
        # Wheel: A-2-3-4-5 (此時 ranks 為 [14, 5, 4, 3, 2]，最大牌為 5)
        elif ranks == [14, 5, 4, 3, 2]:
            is_straight = True
            straight_high = 5

    # 統計牌數頻率
    # 格式：[(頻率, 點數), ...] 並由多到少、由大到小排序
    counts = {r: ranks.count(r) for r in set(ranks)}
    # 優先按張數排序，張數相同按點數由大到小排序
    sorted_by_freq = sorted(counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
    freq_pattern = [item[1] for item in sorted_by_freq]
    freq_ranks = [item[0] for item in sorted_by_freq]

    # 回傳結構: (牌型等級, *比較依據點數)
    # 9: 同花順 (包含皇家同花順，straight_high=14 即為皇家)
    if is_flush and is_straight:
        return (9, straight_high)
    # 8: 四條 (比四條點數，再比單張 kicker)
    if freq_pattern == [4, 1]:
        return (8, freq_ranks[0], freq_ranks[1])
    # 7: 葫蘆 (比三條點數，再比對子點數)
    if freq_pattern == [3, 2]:
        return (7, freq_ranks[0], freq_ranks[1])
    # 6: 同花 (由大到小比全部 5 張)
    if is_flush:
        return (6, *ranks)
    # 5: 順子 (比順子最大的牌)
    if is_straight:
        return (5, straight_high)
    # 4: 三條 (比三條點數，再比另外兩張 kicker)
    if freq_pattern == [3, 1, 1]:
        return (4, freq_ranks[0], freq_ranks[1], freq_ranks[2])
    # 3: 兩對 (比大對、小對，再比單張 kicker)
    if freq_pattern == [2, 2, 1]:
        return (3, freq_ranks[0], freq_ranks[1], freq_ranks[2])
    # 2: 一對 (比對子點數，再依序比三張 kicker)
    if freq_pattern == [2, 1, 1, 1]:
        return (2, freq_ranks[0], freq_ranks[1], freq_ranks[2], freq_ranks[3])
    # 1: 高牌 (依序比全部 5 張)
    return (1, *ranks)

def classify_hand(cards7):
    # 透過 Python tuple 比較特性，直接取 21 種 5 張組合中的最大值
    best_hand = max(classify_5(combo) for combo in combinations(cards7, 5))
    return best_hand