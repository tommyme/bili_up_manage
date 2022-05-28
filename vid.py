class VideoId:
    def __init__(self, id):
        self.bvid = ""
        self.avid = 0
        if type(id) == str and id.startswith('BV'):
            self.bvid = id
        else:
            self.avid = int(id)

    table = 'fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF'
    tr = {}
    for i in range(58):
        tr[table[i]] = i
    s = [11, 10, 3, 8, 4, 6]
    xor = 177451812
    add = 8728348608

    @property
    def av(self):
        if self.avid:
            return self.avid
        r = 0
        for i in range(6):
            r += self.tr[self.bvid[self.s[i]]]*58**i
        self.avid = (r-self.add) ^ self.xor
        return self.avid

    @property
    def bv(self):
        if self.bvid:
            return self.bvid
        x = (self.avid ^ self.xor)+self.add
        r = list('BV1  4 1 7  ')
        for i in range(6):
            r[self.s[i]] = self.table[x//58**i % 58]
        self.avid = ''.join(r)
        return self.avid
