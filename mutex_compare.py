"""
مقایسه ۴ روش انحصار متقابل: Semaphore، Monitor، Peterson، Dekker
دو نخ (Thread) هر کدام N بار یک شمارنده مشترک را افزایش می‌دهند.
اگر انحصار متقابل درست باشد، مقدار نهایی باید دقیقاً 2*N شود.
"""
import sys
import threading
import time

N = 3000  # تعداد افزایش توسط هر نخ
sys.setswitchinterval(1e-5)  # سوییچ سریع‌تر بین نخ‌ها برای دیدن شرایط رقابتی

counter = 0


def critical_section():
    """بخش بحرانی: خواندن-تغییر-نوشتن (غیراتمی)"""
    global counter
    tmp = counter
    time.sleep(0)  # واگذاری CPU تا شرایط رقابتی (race) قابل مشاهده شود
    tmp += 1
    counter = tmp


# ---------- ۰) بدون هماهنگی (برای مقایسه) ----------
class NoLock:
    def enter(self, i): pass
    def exit(self, i): pass


# ---------- ۱) Semaphore ----------
class SemaphoreLock:
    def __init__(self):
        self.sem = threading.Semaphore(1)

    def enter(self, i): self.sem.acquire()
    def exit(self, i): self.sem.release()


# ---------- ۲) Monitor (Condition + متغیر وضعیت) ----------
class MonitorLock:
    def __init__(self):
        self.cond = threading.Condition()
        self.busy = False

    def enter(self, i):
        with self.cond:
            while self.busy:
                self.cond.wait()
            self.busy = True

    def exit(self, i):
        with self.cond:
            self.busy = False
            self.cond.notify()


# ---------- ۳) Peterson ----------
class PetersonLock:
    def __init__(self):
        self.flag = [False, False]
        self.turn = 0

    def enter(self, i):
        j = 1 - i
        self.flag[i] = True
        self.turn = j
        while self.flag[j] and self.turn == j:
            time.sleep(0)  # انتظار فعال (busy waiting)

    def exit(self, i):
        self.flag[i] = False


# ---------- ۴) Dekker ----------
class DekkerLock:
    def __init__(self):
        self.wants = [False, False]
        self.turn = 0

    def enter(self, i):
        j = 1 - i
        self.wants[i] = True
        while self.wants[j]:
            if self.turn != i:
                self.wants[i] = False
                while self.turn != i:
                    time.sleep(0)
                self.wants[i] = True

    def exit(self, i):
        self.turn = 1 - i
        self.wants[i] = False


def worker(lock, i):
    for _ in range(N):
        lock.enter(i)
        critical_section()
        lock.exit(i)


def run(name, lock):
    global counter
    counter = 0
    threads = [threading.Thread(target=worker, args=(lock, i)) for i in (0, 1)]
    start = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.perf_counter() - start
    ok = "✔" if counter == 2 * N else "✘"
    return name, counter, elapsed, ok


if __name__ == "__main__":
    algos = [
        ("No lock (baseline)", NoLock()),
        ("Semaphore", SemaphoreLock()),
        ("Monitor", MonitorLock()),
        ("Peterson", PetersonLock()),
        ("Dekker", DekkerLock()),
    ]
    print(f"Expected value: {2 * N}\n")
    print(f"{'Algorithm':<20}{'Final value':>12}{'Time (s)':>14}{'Correct':>10}")
    print("-" * 56)
    for name, lock in algos:
        n, c, t, ok = run(name, lock)
        print(f"{n:<20}{c:>12}{t:>14.4f}{ok:>10}")
