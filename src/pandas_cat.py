import base64
from io import BytesIO

import pandas
import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pandas.core.dtypes.common import is_categorical_dtype

from jinja2 import Environment, FileSystemLoader

from cleverminer import cleverminer
import scipy.stats as ss


class pandas_cat:
    """
    Pandas categorical profiling. Creates html report with profile of categorical dataset. Provides also other useful functions.
    """

    version_string = "0.1.3"
    template_name = "default_0_1_3.tem"

    def __init__(self):
        """
        Initializes a class.

        """
    @staticmethod
    def profile(df: pandas.DataFrame = None, dataset_name: str = None, template: str = None, opts: dict = None):
        """
        Profiles a categorical dataset.

        :param df: pandas dataframe to profile
        :param dataset_name: dataset name
        :param template: 'default' or 'interactive' template for the final report
        :param opts: options

        Options inlude:
            * **auto_prepare** - set whether to apply automatic dataframe preparation (default = True)
            * **cat_limit** - limit number of categories to profile (default=20)
            * **na_values** - array of additional custom values that should be detected as missing
            * **na_ignore** - array of values (from default list) that should not be detected as missings
            * **keep_default_na** - boolean to completely override the default missing values list
        """
        self = pandas_cat

        # GENERATE INTERACTIVE REPORT
        if template == 'interactive':
            # Use default options if they were not specified by user
            default_options = {'auto_prepare': True,
                               'cat_limit': 20,
                               'na_values': None, 'na_ignore': None, "keep_default_na": True}
            options = default_options if opts is None else {
                **default_options, **opts}

            print('Progress 1/6: Handling missing values...')
            df, detected_missings, replaced_counts = self.handle_missing_values(
                df, options['na_values'], options['na_ignore'], options['keep_default_na'])

            print('Progress 2/6: Preparing attribute profiles...')

            # Storage for attribute profiles
            attribute_profiles = []
            excluded_attributes = []

            # Iterate over each column in df
            for column in df.columns:
                # Count categories
                categories_counts = df[column].value_counts()
                # If categories count is over the limit remove attribute
                if len(categories_counts) > options['cat_limit']:
                    removed_attribute_profile = {
                        "attribute": column, "categories": len(categories_counts)}
                    excluded_attributes.append(removed_attribute_profile)
                    df.drop(column, axis=1, inplace=True)
                    continue
                # Count missing values
                missing_count = df[column].isna().sum()
                # Get RAM usage
                formated_ram = self._humanbytes(
                    df.memory_usage(deep=True)[column])
                # Create profile for the attribute
                profile = {
                    'attribute': column,
                    'categories': categories_counts.index.tolist(),
                    'counts': [int(val) for val in categories_counts.values.tolist()],
                    'percentages': [float(round((val / (categories_counts.values.sum() + missing_count)) * 100, 2)) for val in categories_counts.values.tolist()],
                    'missing': int(missing_count),
                    'ram': formated_ram,
                    'detected': [str(val) for val in detected_missings[column]],
                    'replaced': [int(val) for val in replaced_counts[column]]
                }
                # Store profile
                attribute_profiles.append(profile)

            print('Progress 3/6: Calculating overall correlations...')

            # Storage for correlations
            correlations_data = {}
            correlations_data['Cramers V'] = []
            correlations_data['Spearman Rank'] = []
            correlations_data['Theils U'] = []

            for column_one in df.columns:
                for column_two in df.columns:
                    # Calculate Cramer's V
                    confusion_matrix = pd.crosstab(
                        df[column_one], df[column_two])
                    cramers_v = round(
                        float(self._cramers_corrected_stat(confusion_matrix)), 3)
                    entry_cramers = {"x": column_one,
                                     "y": column_two, "v": cramers_v}
                    correlations_data['Cramers V'].append(entry_cramers)

                    # Convert categorical data to numeric codes for Spearman rank correlation
                    col_one = df[column_one]
                    col_two = df[column_two]
                    if col_one.dtype == 'object' or is_categorical_dtype(col_one):
                        col_one = col_one.astype('category').cat.codes
                    if col_two.dtype == 'object' or is_categorical_dtype(col_two):
                        col_two = col_two.astype('category').cat.codes

                    # Calculate Spearman rank correlation
                    spearman_corr, _ = ss.spearmanr(
                        col_one, col_two, nan_policy='omit')
                    if spearman_corr != spearman_corr:  # replace NaN with 0
                        spearman_corr = 0
                    spearman_corr = round(float(spearman_corr), 3)
                    entry_spearman = {"x": column_one,
                                      "y": column_two, "v": spearman_corr}
                    correlations_data['Spearman Rank'].append(entry_spearman)

                    # Calculate Theil's U
                    theils_u = round(float(self._theils_u(
                        df[column_one], df[column_two])), 3)
                    entry_theils_u = {"x": column_one,
                                      "y": column_two, "v": theils_u}
                    correlations_data['Theils U'].append(entry_theils_u)

            print('Progress 4/6: Calculating individual correlations...')

            # Iterate over each combination of columns
            for i, column_one in enumerate(df.columns):
                for j, column_two in enumerate(df.columns):
                    confusion_matrix = pd.crosstab(
                        df[column_one], df[column_two])
                    crosstab_data = confusion_matrix.to_dict(orient='split')
                    # Iterate over each combination of categories
                    for k, category_one in enumerate(crosstab_data['index']):
                        for l, category_two in enumerate(crosstab_data['columns']):
                            correlation = float(crosstab_data['data'][k][l])
                            entry = {"x": category_one,
                                     "y": category_two, "v": correlation}
                            key = f"{column_one} x {column_two}"
                            if key not in correlations_data:
                                correlations_data[key] = []
                            correlations_data[key].append(entry)

            print('Progress 5/6: Preparing html report...')

            # Load Jinja2 template
            env = Environment(loader=FileSystemLoader(
                f"{os.path.dirname(__file__)}/templates/interactive"))
            template = env.get_template('interactive.html')

            # Ready input data for the template
            data = {
                'title': dataset_name or 'DataFrame',
                'excluded_attributes': excluded_attributes,
                'attribute_profiles': attribute_profiles,
                'correlations_data': correlations_data,
                'attribute_count': df.shape[1],
                'records_count': df.shape[0],
                'missing_count': df.isnull().sum().sum(),
                'total_ram': self._humanbytes(df.memory_usage(deep=True).sum())
            }

            # Render html using the template
            html = template.render(**data)

            # Write result in the file
            report_dir = os.path.join(os.getcwd(), 'report')
            if not os.path.exists(report_dir):
                os.makedirs(report_dir)
            filename = os.path.join(report_dir, f'{dataset_name.lower()}.html')
            with open(filename, 'w') as f:
                f.write(html)

            # Prepare dataset if auto_prepare is on
            if options['auto_prepare'] is True:
                df = self.prepare(df)

            print(
                f'Progress 6/6: Report {dataset_name.lower()}.html finished...')
            return

        # GENERATE DEFAULT REPORT
        my_df = df
        if not (type(df) == pandas.core.frame.DataFrame):
            print("Cannot profile. Parameter df is not a pandas dataframe.")
            return

        # Use default options if they were not specified by user
        default_options = {'auto_prepare': True,
                           'cat_limit': 20,
                           'na_values': None, 'na_ignore': None, "keep_default_na": True}
        options = default_options if opts is None else {
            **default_options, **opts}

        my_df, _, _ = self.handle_missing_values(
            df, options['na_values'], options['na_ignore'], options['keep_default_na'])

        if opts is not None:
            if "auto_prepare" in opts:
                if opts.get("auto_prepare") == True or opts.get("auto_prepare") == 1:
                    print("Will auto prepare data...")
                    my_df = self.prepare(df=my_df, opts=opts)
                    print("... auto prepare data done.")
        df = my_df

        warning_info = []

        # check limit on number of categories for each variable

        limit = 20

        if opts is not None:
            if "cat_limit" in opts:
                limit = opts.get("cat_limit")
        print(f"Will limit to {limit} categories.")

        to_drop = []

        for var in df.columns:
            dff = df[var]
            lst = dff.unique()
            cnt = len(lst)
            print(f"...variable {var} has {cnt} categories")
            if cnt > limit:
                print(f"WARNING: variable {var} has been removed from profiling because it has {cnt} categories, which is over limit {
                      limit}. Note you may increase the limit of allowed categories by setting the parameter cat_limit.")
                warning_info.append({'type': 'alert-warning', 'text': 'WARNING: variable '+var+' has been removed from profiling because it has '+str(
                    cnt)+' categories, which is over the limit of '+str(limit)+' categories.<br> Note you may increase the limit of allowed categories by setting the parameter <i>cat_limit</i>.'})
                to_drop.append(var)
            if cnt == 1 and lst[0] != lst[0]:
                print(
                    f"WARNING: variable {var} has been removed from profiling because it has only empty value.")
                warning_info.append({'type': 'alert-warning', 'text': 'WARNING: variable ' +
                                    var+' has been removed from profiling because it has only empty value.'})
                to_drop.append(var)
            if cnt == 0:
                print(
                    f"WARNING: variable {var} has been removed from profiling because it has {cnt} categories")
                warning_info.append({'type': 'alert-warning', 'text': 'WARNING: variable '+var +
                                    ' has been removed from profiling because it has '+str(cnt)+' categories.'})
                to_drop.append(var)
            # or isinstance(var,dict):
            if isinstance(var, list) or isinstance(var, tuple):
                print(
                    f"WARNING: variable {var} has been removed from profiling because it has unsupported type ({type(var)})")
                warning_info.append({'type': 'alert-warning', 'text': 'WARNING: variable '+var +
                                    ' has been removed from profiling because it has unsupported type ('+type(var)+').'})
                to_drop.append(var)

        if len(to_drop) > 0:
            print(f"...will drop {to_drop}")
            df = df.drop(columns=to_drop)

        env = Environment(loader=FileSystemLoader(
            os.path.dirname(__file__)+'/'+'templates'))
        html_inner = ""
        indi_variables = []

        cntordr = 0

        print("Preparing summary...")
        size = df.memory_usage(deep=True).sum()
        size_str = str(f'{self._humanbytes(size)}')

        df_summary = {}
        df_summary['overall_table'] = {'Records': str(f'{len(df):,}'), 'Columns': str(
            f'{len(df.columns):,}'), 'Memory usage': size_str}

        varlist = df.columns

        summ_vars = []

        tmp_colname_for_chart = []
        tmp_name_for_chart = []
        tmp_val_for_chart = []
        lst_for_df = []

        for var in varlist:
            dff = df[var]
            var_size = dff.memory_usage(deep=True)
            var_size_str = str(f'{self._humanbytes(var_size)}')
            dfg = df.groupby(var)
            cat_list = ""
            cat_cnt = 0
            for grp_name, grp_rows in dfg:
                if cat_cnt > 0:
                    cat_list = cat_list + ", "
                cat_list = cat_list + str(grp_name)
                cat_cnt += 1
            var_item = {'Attribute': var, 'Categories': cat_cnt, 'Categories_list': cat_list, 'Memory_usage': var_size,
                        'Memory_usage_hr': var_size_str}
            summ_vars.append(var_item)
            tmp_name_for_chart.append(var)
            tmp_colname_for_chart.append('Memory usage')
            tmp_val_for_chart.append(var_size)
            lst_for_df_sub = []
            lst_for_df_sub.append(var)
            lst_for_df_sub.append(var_size)
            lst_for_df.append(lst_for_df_sub)

        df_summary['Profiles'] = summ_vars

        # in following code we will not use _humanbytes as we need same unit for all items
        unit = "Bytes"
        tot_size = sum(tmp_val_for_chart)
        min_splitter = 3
        if tot_size > min_splitter * 1000000000000:
            unit = "TB"
            tmp_val_for_chart = [x / 1000000000000 for x in tmp_val_for_chart]
        elif tot_size > min_splitter * 1000000000:
            unit = "GB"
            tmp_val_for_chart = [x / 1000000000 for x in tmp_val_for_chart]
        elif tot_size > min_splitter * 1000000:
            unit = "MB"
            tmp_val_for_chart = [x / 1000000 for x in tmp_val_for_chart]
        elif tot_size > min_splitter * 1000:
            unit = "KB"
            tmp_val_for_chart = [x / 1000 for x in tmp_val_for_chart]

        tmp_name_for_chart.insert(0, "Memory usage")
        tmp_val_for_chart.insert(0, "")

        tmp_val_for_chart2 = []
        tmp_val_for_chart2.append(tmp_val_for_chart)

        tmp_df2 = pd.DataFrame(tmp_val_for_chart2, columns=tmp_name_for_chart)

        tmp_df2.plot(x='Memory usage', kind='bar', stacked=True,
                     title='Memory usage by attribute')

        # reordering the labels
        handles, labels = plt.gca().get_legend_handles_labels()

        # specify order
        order = list(range(len(varlist)))
        order.reverse()

        # set legend and labels

        plt.legend([handles[i] for i in order], [labels[i]
                   for i in order], bbox_to_anchor=(1, 1), loc=2, borderaxespad=0.)
        plt.tight_layout()
        plt.ylabel('Size in ' + unit)

        # save to stream

        tmpfile = BytesIO()
        plt.savefig(tmpfile, format='svg')
        encoded = base64.b64encode(tmpfile.getvalue()).decode('utf-8')
        df_summary['mem_usg_svg'] = encoded

        print("Preparing summary...done")
        print("Preparing individual profiles...")

        for i in df.columns:
            df2 = df[[i]]
            cntordr += 1
            for j in df2.columns:
                fcont = self._plot_histogram(
                    df2, j, sort=False, save=False, rotate=False)
                df3 = df2.groupby(j)

                is_ordered = False

                if is_categorical_dtype(df[i]):
                    if df[i].cat.ordered:
                        is_ordered = True

                most_frequent = None
                for grp_name, grp_rows in df3:
                    if most_frequent is None or most_frequent < len(grp_rows):
                        most_frequent = len(grp_rows)

                freq_tbl = []

                for grp_name, grp_rows in df3:
                    pct = len(grp_rows) / len(df2) * 100
                    fmt_width = len(grp_rows) / most_frequent * 100
                    pct_str = str(f'%.2f%%' % pct)
                    fmt_width_str = str(f'%.2f%%' % fmt_width)

                    freq_tbl_item = {'name': grp_name, 'count': len(grp_rows), 'pct': pct_str, 'pct_num': pct,
                                     'fmt_width': fmt_width_str}
                    freq_tbl.append(freq_tbl_item)

                fn = j + ".svg"
                summary = ""
                summary_tbl = {}
                summary += "Categories : " + str(len(df2[j].unique())) + "<br>"
                summary_tbl['Categories'] = str(len(df2[j].unique()))
                idxmax = df[j].value_counts().idxmax()
                idxmin = df[j].value_counts().idxmin()
                cnt_max = len(df2[df2[j] == idxmax])
                pct_max = cnt_max / len(df2) * 100
                cnt_min = len(df2[df2[j] == idxmin])
                pct_min = cnt_min / len(df2) * 100
                summary += "Most frequent : " + str(idxmax) + " (" + str(f'{cnt_max:,}') + " values, " + str(
                    f'%.2f%%' % pct_max) + ")<br>"
                summary_tbl['Most frequent'] = str(idxmax) + " (" + str(f'{cnt_max:,}') + " values, " + str(
                    f'%.2f%%' % pct_max) + ")"
                summary += "Least frequent : " + str(idxmin) + " (" + str(f'{cnt_min:,}') + " values, " + str(
                    f'%.2f%%' % pct_min) + ")<br>"
                summary_tbl['Least frequent'] = str(idxmin) + " (" + str(f'{cnt_min:,}') + " values, " + str(
                    f'%.2f%%' % pct_min) + ")"
                size = df2.memory_usage(deep=True).sum()
                size_str = str(f'{self._humanbytes(size)}')
                summary_tbl['mem_usage'] = size_str
                missings = df2[j].isna().sum()
                missings_pct = missings / len(df2) * 100
                summary += "Missings: " + \
                    str(f'{missings:,}') + \
                    " (" + str(f'%.2f%%' % missings_pct) + ")<br>"
                summary_tbl['Missings'] = str(
                    f'{missings:,}') + " (" + str(f'%.2f%%' % missings_pct) + ")"
                d = {'varname': j, 'is_ordered': is_ordered, 'freq_table': None, 'freq_chart': None, 'fname': fn, 'fcont': fcont,
                     'cnt': cntordr, 'summary': summary, 'summary_tbl': summary_tbl, 'freq_tbl': freq_tbl}
                indi_variables.append(d)

        print("Preparing individual profiles...done")
        print("Preparing overall correlations...")

        # https://stackoverflow.com/questions/20892799/using-pandas-calculate-cram%C3%A9rs-coefficient-matrix
        dict_cramer = {'col1': [], 'col2': [], 'cnt': []}
        df_cramer = pd.DataFrame(dict_cramer)

        for i in df.columns:
            for j in df.columns:
                confusion_matrix = pd.crosstab(df[i], df[j])
                cr = self._cramers_corrected_stat(
                    confusion_matrix=confusion_matrix)
                df2 = pd.DataFrame({'col1': [i], 'col2': [j], 'cnt': [cr]})
                # df_cramer.append(df2,ignore_index=True)
                df_cramer = pd.concat(
                    [df_cramer, df2], axis=0, ignore_index=True)
        ct = pd.crosstab(df_cramer['col1'], df_cramer['col2'],
                         values=df_cramer['cnt'], aggfunc='mean')
        plt.figure(figsize=(16, 4))
        sns.heatmap(ct, annot=True, cmap='Blues', fmt='.2f', linewidth=1)
        tmpfile_c_o = BytesIO()
        plt.savefig(tmpfile_c_o, format='svg')
        plt.close()
        encoded_c_o = base64.b64encode(tmpfile_c_o.getvalue()).decode('utf-8')
        overall_corr = encoded_c_o

        print("Preparing overall correlations...done")
        print("Preparing individual correlations...")
        indiv_corr = {}

        for i in df.columns:
            print(f"... for variable {i}...")
            dict = {'varname': i}
            dict2 = {}
            for j in df.columns:
                ct = pd.crosstab(df[i], df[j])
                print(f"...... doing crosstab {i} x {j}")
                plt.figure(figsize=(16, 4))
                sns.heatmap(ct, annot=True, cmap='Blues', fmt='g')
                tmpfile_c_i = BytesIO()
                plt.savefig(tmpfile_c_i, format='svg')
                plt.close()
                encoded_c_i = base64.b64encode(
                    tmpfile_c_i.getvalue()).decode('utf-8')
                dict2[j] = encoded_c_i

            dict['vars'] = dict2
            indiv_corr[i] = dict

        corr = {}
        corr['overall_corr'] = overall_corr
        corr['indiv_corr'] = indiv_corr

        print("Preparing individual correlations...done.")
        print("Preparing output file...")

        fname = "report.html"

        outdir = os.path.join(os.getcwd(), 'report')
        # Check whether the specified path exists or not
        isExist = os.path.exists(outdir)
        if not isExist:
            # Create a new directory because it does not exist
            os.makedirs(outdir)
            print("The new directory is created!")
        outname = os.path.join(os.getcwd(), 'report', fname)

        # Load the template from the Environment

        template = env.get_template(self.template_name)

        dn = dataset_name

        if dn is None:
            dn = '&lt;pandas dataframe&gt;'

        html = template.render(dataset_name=dn,
                               warning_info=warning_info,
                               df_summary=df_summary,
                               indi_variables=indi_variables,
                               corr=corr,
                               version_string=pandas_cat.version_string
                               )

        with open(outname, 'w') as f:
            f.write(html)
        print("Preparing output file ...done")
        print("Finished preparing profile report.")
        print(f"Your report is ready in file {outname}")

    def _cramers_corrected_stat(confusion_matrix):
        """ calculate Cramers V statistic for categorial-categorial association.
            uses correction from Bergsma and Wicher,
            Journal of the Korean Statistical Society 42 (2013): 323-328
        """
        chi2 = ss.chi2_contingency(confusion_matrix)[0]
        n = confusion_matrix.sum().sum()
        phi2 = chi2 / n
        r, k = confusion_matrix.shape
        phi2corr = max(0, phi2 - ((k - 1) * (r - 1)) / (n - 1))
        rcorr = r - ((r - 1) ** 2) / (n - 1)
        kcorr = k - ((k - 1) ** 2) / (n - 1)

        denominator = min((kcorr - 1), (rcorr - 1))
        if denominator <= 0:
            return 0

        return np.sqrt(phi2corr / denominator)

    def _theils_u(x, y):
        """Calculate Theil's U statistic for categorical-categorical association."""
        from collections import Counter
        import math

        def conditional_entropy(x, y):
            """Calculates conditional entropy."""
            y_counter = Counter(y)
            xy_counter = Counter(list(zip(x, y)))
            total_occurrences = sum(y_counter.values())
            entropy = 0
            epsilon = np.finfo(float).eps

            for xy in xy_counter.keys():
                p_xy = xy_counter[xy] / total_occurrences
                p_y = y_counter[xy[1]] / total_occurrences
                p_x_given_y = p_xy / (p_y + epsilon)
                entropy += p_xy * math.log(p_x_given_y, 2)

            return -entropy

        H_xy = conditional_entropy(x, y)
        x_counter = Counter(x)
        total_occurrences = sum(x_counter.values())
        p_x = list(map(lambda count: count /
                   total_occurrences, x_counter.values()))
        H_x = ss.entropy(p_x, base=2)

        return (H_x - H_xy) / H_x if H_x != 0 else 0

    def _plot_histogram(df, column, sort=False, save=False, save_folder=None, rotate=True):
        label_format = '{:,.0f}'
        data = df
        if sort:
            data = data.sort_values(by=column)
        grp = data.groupby(column, dropna=False)[column].count()

        plt.figure(figsize=(16, 4))
        a = sns.barplot(x=grp.index, y=grp.values,
                        color="lightsteelblue", edgecolor="black")
        if rotate:
            plt.xticks(rotation=90)

        ticks_loc = a.get_yticks().tolist()
        a.yaxis.set_major_locator(mticker.FixedLocator(ticks_loc))
        a.set_yticklabels([label_format.format(x) for x in ticks_loc])
        plt.tight_layout()
        if save:
            filename = ""
            if save_folder is not None:
                filename = save_folder+'\\'
            filename = filename+column+'.svg'
            plt.savefig(filename)
        else:
            tmpfile = BytesIO()
            plt.savefig(tmpfile, format='svg')
            encoded = base64.b64encode(tmpfile.getvalue()).decode('utf-8')
            fcont = encoded
            return fcont

    def _humanbytes(B):
        """Return the given bytes as a human friendly KB, MB, GB, or TB string."""
        power = 2**10
        n = 0
        power_labels = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}

        while B > power:
            B /= power
            n += 1

        return f"{B:.2f} {power_labels[n]}"

    @staticmethod
    def prepare(df: pandas.DataFrame = None, opts: dict = None,auto_data_prep='CLM'):
        """
        Prepares a categorical dataset. Takes strings, integers etc. variables and if possible, converts it do
        pandas categorical and ordered by their natural value

        :param df: pandas dataframe to prepare (advance) in pandas categorical


        """
        #currently we are moving CleverMiner's data preparation to here, default for now remains CleverMiner's data preparation
        #we plan to create this package independent on CleverMiner package and make this as a master for data preparation        
        
        my_df = df
        opts2 = opts
        if opts2 is None:
            opts2 = {}
        opts2['keep_df'] = True
        if auto_data_prep=='CLM':
            clm = cleverminer(df=my_df, opts=opts2)
            if cleverminer.version_string < '1.0.7':
                return my_df
            return clm.df
        else:
            return pandascat._automatic_data_conversions(df)

    def _automatic_data_conversions(df:pandas.DataFrame=None):
        self=pandas_cat
        print("Automatically reordering numeric categories ...")
        for i in range(len(df.columns)):
            if self.verbosity['debug']:
                print(f"#{i}: {df.columns[i]} : {df.dtypes[i]}.")
            try:
                df[df.columns[i]] = df[df.columns[i]].astype(str).astype(float)
                if self.verbosity['debug']:
                    print(f"CONVERTED TO FLOATS #{i}: {df.columns[i]} : {df.dtypes[i]}.")
                lst2 = pd.unique(df[df.columns[i]])
                is_int = True
                for val in lst2:
                    if val % 1 != 0:
                        is_int = False
                if is_int:
                    df[df.columns[i]] = df[df.columns[i]].astype(int)
                    if self.verbosity['debug']:
                        print(f"CONVERTED TO INT #{i}: {df.columns[i]} : {df.dtypes[i]}.")
                lst3 = pd.unique(df[df.columns[i]])
                cat_type = CategoricalDtype(categories=lst3.sort(), ordered=True)
                df[df.columns[i]] = df[df.columns[i]].astype(cat_type)
                if self.verbosity['debug']:
                    print(f"CONVERTED TO CATEGORY #{i}: {df.columns[i]} : {df.dtypes[i]}.")

            except:
                if self.verbosity['debug']:
                    print("...cannot be converted to int")
                try:
                    values = df[df.columns[i]].unique()
                    if self.verbosity['debug']:
                        print(f"Values: {values}")
                    is_ok = True
                    extracted = []
                    for val in values:
                        #                        print(f"...will process {val}")
                        #                        res = re.findall(r"[-+]?(?:\d*\.*\d+)", val)
                        res = re.findall(r"-?\d+", val)
                        #                        print(f"...found {res}")
                        if len(res) > 0:
                            extracted.append(int(res[0]))
                        else:
                            is_ok = False
                    if self.verbosity['debug']:
                        print(f"Is ok: {is_ok}, extracted {extracted}")
                    if is_ok:
                        extracted_sorted = copy.deepcopy(extracted)
                        extracted_sorted.sort()
                        #                       print(f"DBG1: {extracted_sorted}, {extracted}")
                        sorted_list = []
                        for nb in extracted_sorted:
                            idx = extracted.index(nb)
                            #                            print(f"DBG2 {nb} - idx = {idx}")
                            sorted_list.append(values[idx])
                        if self.verbosity['debug']:
                            print(f"Sorted list: {sorted_list}")
                        cat_type = CategoricalDtype(categories=sorted_list, ordered=True)
                        df[df.columns[i]] = df[df.columns[i]].astype(cat_type)


                except:
                    if self.verbosity['debug']:
                        print("...cannot extract numbers from all categories")

        print("Automatically reordering numeric categories ...done")
        return df

            
    @staticmethod
    def handle_missing_values(df, na_values: list = [], na_ignore: list = [], keep_default_na: bool = True):
        """
        Replaces missing string values with real missing values.

        :param df: pandas dataframe
        :param na_values: array of additional custom values that should be also detected as missing values
        :param na_ignore: array of default values to be removed from the list of missing values
        :param keep_default_na: if True, the default missing values will be retained, otherwise, only custom values will be used
        """
        default_missing_values = ['-1.#IND', '1.#QNAN', '1.#IND', '-1.#QNAN', '#N/A N/A', '#N/A', 'N/A',
                                  'n/a', 'NA', 'na', '<NA>', '#NA', 'NULL', 'null', 'Null', 'NAN', 'NaN',
                                  '-NaN', 'nan', '-nan', 'NONE', 'None', 'none', 'UNKNOWN', 'Unknown', 'unknown',
                                  'UNKNOWN/INVALID', 'Unknown/Invalid', 'Unknown/invalid', 'unknown/invalid',
                                  'INVALID', 'Invalid', 'invalid', 'UNAVAILABLE', 'Unavailable', 'unavailable',
                                  'MISSING', 'Missing', 'missing', 'UNSPECIFIED', 'Unspecified', 'unspecified',
                                  'IGNORE', 'Ignore', 'ignore', 'NO INFO', 'NO_INFO', 'No Info', 'No info', 'no info',
                                  'no_info', 'UNDETERMINED', 'Undetermined', 'undetermined', 'NOT GIVEN',
                                  'UNDEFINED', 'Undefined', 'undefined', 'NOT DEFINED', 'Not Defined', 'Not defined',
                                  'not_defined', 'NOT_GIVEN', 'Not Given', 'Not given', 'not given', 'not_given', 'UNSURE',
                                  'Unsure', 'unsure', 'I WOULD RATHER NOT SAY', 'I would rather not say',
                                  'i would rather not say', 'NO DEFINIDO', 'No Definido', 'No definido', 'no definido',
                                  'no_definido', 'NO COLOR', 'No Color', 'No color', 'no color', 'no_color',
                                  'NOT RATED', 'NR', 'Not Rated', 'Not rated', 'not rated', 'not_rated', 'nr',
                                  '""', '?', '–', '-', '']
        if na_ignore:
            default_missing_values = [
                value for value in default_missing_values if value not in na_ignore]

        missing_values = default_missing_values if keep_default_na else []

        if na_values:
            missing_values.extend(na_values)

        detected_missing_values = {}
        replaced_counts = {}

        for column in df.columns:
            categories_counts = df[column].value_counts()
            missing_counts = categories_counts[categories_counts.index.isin(
                missing_values)]

            detected_missing_values[column] = []
            replaced_counts[column] = []

            detected_missing_values[column] = missing_counts.index.tolist()
            replaced_counts[column] = missing_counts.values.tolist()

            na_already_detected_by_pandas = df[column].isna().sum()
            if na_already_detected_by_pandas > 0:
                detected_missing_values[column].insert(
                    0, 'pandas.NAN')
                replaced_counts[column].insert(0, df[column].isna().sum())

            df[column].replace(missing_values, pd.NA, inplace=True)

        return df, detected_missing_values, replaced_counts
