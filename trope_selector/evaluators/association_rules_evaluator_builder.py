import bz2
import json

from mlxtend.frequent_patterns import association_rules


class AssociationRulesBuilder(object):
    def __init__(self, extended_dataset_resource, output_prefix, min_support=0.005, min_threshold=0.8):
        self.extended_dataset_resource = extended_dataset_resource
        self.output_prefix = output_prefix
        self.min_support = min_support
        self.min_threshold = min_threshold
        self.extended_dataset = None

    def prepare(self):
        with open(self.extended_dataset_resource, 'rb') as file:
            compressed_content = file.read()
        csv_content = bz2.decompress(compressed_content)
        self.extended_dataset = json.loads(csv_content)

    def build_rules(self):
        baskets = [element['tropes'] for element in self.extended_dataset]
        import pandas as pd
        from mlxtend.preprocessing import TransactionEncoder

        te = TransactionEncoder()
        te_ary = te.fit(baskets).transform(baskets)
        df = pd.DataFrame(te_ary, columns=te.columns_)

        from mlxtend.frequent_patterns import fpgrowth

        support_items = fpgrowth(df, min_support=self.min_support, use_colnames=True)
        rules = association_rules(support_items, metric='confidence', min_threshold=self.min_threshold,
                                  support_only=False)
        print(f'Rules shape: {rules.shape}')

        file_parameters = f'[{self.min_support}, {self.min_threshold}]'.replace('.', '_')
        file_name = f'{self.output_prefix}_{file_parameters}.csv.bz2'
        rules.to_csv(file_name, index = False, header=True, compression='bz2')

        print(f'Compressed JSON written to {file_name}')
