from random import Random


class RandomWordGenerator(object):
    CONSONANTS = [chr(i + 97) for i in range(26)] + ["", ""]
    VOWELS = ["a", "e", "i", "o", "u"]

    def __init__(self, random: Random) -> None:
        self.random = random

    def get_character_name(self):
        letters = []
        number_of_syllables = self.random.randint(3, 4)
        for syllable in range(0, number_of_syllables):
            letters.append(self.random.choice(self.CONSONANTS))
            letters.append(self.random.choice(self.VOWELS))
        return ''.join(letters).capitalize()

    def get_place_name(self):
        # from https://www.enchantedlearning.com/geography/landforms/glossary.shtml
        landforms = ['archipelago', 'atoll', 'bay', 'butte', 'canyon', 'cape', 'cave', 'cay', 'channel', 'cliff', 'col',
                     'cove', 'delta', 'desert', 'dune', 'estuary', 'fjord', 'geyser', 'glacier', 'gulf',
                     'hill', 'island', 'isthmus', 'key', 'lagoon', 'lake', 'marsh', 'mesa', 'mountain', 'peninsula',
                     'plain', 'plateau', 'pond', 'prairie', 'river', 'sea', 'sound', 'source', 'strait', 'swamp',
                     'tributary', 'tundra', 'valley', 'volcano', 'waterfall', 'wetland', 'beach']
        communities = ['Megalopolis', 'Megacity', 'Conurbation', 'Global city', 'Metropolis', 'Municipality',
                       'Regiopolis', 'City', 'Prefecture', 'County', 'Borough', 'District', 'Town', 'Shire', 'Township',
                       'Subdistrict', 'Suburb', 'Locality', 'Village', 'Tribe', 'Hamlet', 'Band', 'Homestead',
                       'Neighbourhood', 'Roadhouse', 'Bed and breakfast']

        letters = []
        number_of_syllables = self.random.randint(3, 4)
        for syllable in range(0, number_of_syllables):
            letters.append(self.random.choice(self.CONSONANTS))
            letters.append(self.random.choice(self.VOWELS))
        name = ''.join(letters)
        return ' '.join([self.random.choice(landforms + communities).capitalize(), name.capitalize()])


if __name__ == '__main__':
    random = Random(x=0)
    generator = RandomWordGenerator(random)
    for i in range(0, 10):
        print(generator.get_character_name())
