from sortedcontainers import SortedSet


class SortedSetKey:
    def __init__(self, d):
        self.dict = d
        self.sorted_set = SortedSet(key=self.__key)

    def __getitem__(self, item):
        return self.sorted_set[item]

    def __len__(self):
        return len(self.sorted_set)

    def __str__(self):
        return str(self.sorted_set)

    def __key(self, value):
        return self.dict[value]

    def values(self):
        for value in self.sorted_set:
            yield value

    def clear(self):
        self.sorted_set.clear()
        self.dict.clear()

    def destroy(self):
        self.sorted_set = None

    def index(self, value):
        return self.sorted_set.index(value)

    def pop(self, index=-1):
        return self.sorted_set.pop(index)

    def add(self, value, rank):
        if value in self.sorted_set:
            self.sorted_set.remove(value)
        self.dict[value] = rank
        self.sorted_set.add(value)

    def remove(self, value):
        self.sorted_set.remove(value)
        del self.dict[value]

    def update(self, value_list, rank_list):
        self.sorted_set.difference_update(value_list)
        for i, value in enumerate(value_list):
            self.dict[value] = rank_list[i]
        self.sorted_set.update(value_list)
