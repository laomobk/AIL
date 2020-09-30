import time


class Timer:
    def __init__(self, where: str):
        self.__lt = 0
        self.__time_table = []
        self.__where = where

    def start(self):
        self.__lt = time.time() * 1000

    def lap(self, opname):
        nt = time.time() * 1000
        t = nt - self.__lt

        self.__lt = nt

        self.__time_table.append((opname, t))

        return t

    def print_analytical_table(self):
        print('\n%s 分析表：\n' % self.__where)
        try:
            self.__print_analytical_table()
        except:
            pass

    def __print_analytical_table(self):
        table = {}

        for n, t in self.__time_table:
            t = [t]
            if n in table:
                table[n] += t
            else:
                table[n] = t

        info_table = {n: (sum(x) / len(x), len(x))
                      for n, x in table.items()}

        sum_ct = sum([sum(x) for _, x in table.items()])

        sorted_t = sorted({k: v[0] for k, v in info_table.items()}.items(),
                          key=lambda x: x[1], reverse=True)

        sorted_ts = sorted({k: v[1] for k, v in info_table.items()}.items(),
                           key=lambda x: x[1], reverse=True)

        sorted_tt = sorted({k: sum(v) for k, v in table.items()}.items(),
                           key=lambda x: x[1], reverse=True)

        sorted_ct = sorted({k: round((sum(v) / sum_ct) * 100, 5) for k, v in table.items()}.items(),
                           key=lambda x: x[1], reverse=True)

        avg_t = [x[1] for x in sorted_t]
        avg_t = sum(avg_t) / len(avg_t)

        import pprint

        # pprint.pprint(info_table)
        print('每个字节码调用所用的平均时间 (ms):')
        pprint.pprint(sorted_t)

        print('\n每个字节码调用的次数 (ms)：')
        pprint.pprint(sorted_ts)

        print('\n每个字节码调用次数占比 (%)：')
        pprint.pprint(sorted_ct)

        print('\n每个字节码的总用时 (ms)：')
        pprint.pprint(sorted_tt)

        print('\n平均字节码周期：%s (ms)' % avg_t)
