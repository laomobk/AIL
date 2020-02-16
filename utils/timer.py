import time


class Timer:
    def __init__(self):
        self.__lt = 0
        self.__time_table = []

    def start(self):
        self.__lt = time.time() * 1000

    def lap(self, opname):
        nt = time.time() * 1000
        t = nt - self.__lt

        self.__lt = nt

        self.__time_table.append((opname, t))

        return t

    def print_analytical_table(self):
        table = {}

        for n, t in self.__time_table:
            t = [t]
            if n in table:
                table[n] += t
            else:
                table[n] = t

        info_table = {n : (sum(x) / len(x), len(x)) 
                        for n, x in table.items()}

        sorted_t = sorted({k : v[0] for k, v in info_table.items()}.items(),
                key=lambda x : x[1], reverse=True)

        sorted_ts = sorted({k : v[1] for k, v in info_table.items()}.items(),
                key=lambda x : x[1], reverse=True)

        avg_t = [x[1] for x in sorted_t]
        avg_t = sum(avg_t) / len(avg_t)

        import pprint
        
        # pprint.pprint(info_table)
        print('每个字节码调用所用的平均时间 (ms):')
        pprint.pprint(sorted_t)

        print('\n每个字节码调用的次数：')
        pprint.pprint(sorted_ts)

        print('\n平均字节码周期：%s' % avg_t)
