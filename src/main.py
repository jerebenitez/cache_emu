import cache.cache as c


if __name__ == "__main__":
    mem = c.FileMainMemory("mem.bin", 1024)
    print(mem.read(104))
    mem.write(123, 104)
    print(mem.read(104))
