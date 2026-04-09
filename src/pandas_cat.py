import base64
import copy
import re
from io import BytesIO

import pandas
import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from jinja2 import Environment, FileSystemLoader

from cleverminer import cleverminer
import scipy.stats as ss
from pandas.api.types import CategoricalDtype


class pandas_cat:
    """
    Pandas categorical profiling. Creates html report with profile of categorical dataset. Provides also other useful functions.
    """

    version_string = "0.1.4"
    template_name = "default_0_1_3.tem"

    def __init__(self):
        """
        Initializes a class.

        """
    @staticmethod
    def profile(df: pandas.DataFrame = None, dataset_name: str = None, template: str = None, out_html: str ="report.html" , opts: dict = None):
        """
        Profile a categorical dataset and write an HTML report.

        The report is written to ``<cwd>/report/<out_html>``.  The directory is
        created automatically if it does not exist.

        :param df: DataFrame to profile.
        :param dataset_name: Title shown in the report header.
        :param template: Report template to use.  Accepted values:

            * ``None`` or ``'default'`` — static HTML with embedded SVG charts
              and Cramer's V heatmaps.
            * ``'interactive'`` — interactive report with multiple correlation
              metrics.

        :param out_html: Output filename (basename only, no path).  The file is
            written under ``report/``.  Defaults to ``'report.html'``.
        :param opts: Optional dictionary of settings:

            * **auto_prepare** (*bool*, default ``True``) — tries to automatically
              order all ordinal variables.
            * **cat_limit** (*int*, default ``20``) — maximum categories
              for variable to be included in the report.
            * **na_values** (*list*) — additional strings to treat as missing
              on top of the built-in list.
            * **na_ignore** (*list*) — strings from the built-in missing-value
              list that should *not* be treated as a missing value.
            * **keep_default_na** (*bool*, default ``True``) — whether to use
              the built-in list on the top of na_values (default is True).

        :returns: ``None``.  The report is written to disk.
        """
        self = pandas_cat

        my_df = df
        auto_prepare = True #default

        if opts is not None:
            if "auto_prepare" in opts:
                if opts.get("auto_prepare") == False or opts.get("auto_prepare") == 0:
                    auto_prepare = False

        if auto_prepare:
            print("Will auto prepare data...")
            my_df = self.prepare(df=my_df, opts=opts)
            print("... auto prepare data done.")
            df = my_df


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
                # Count categories, respecting ordered categorical order
                if hasattr(df[column], 'cat') and df[column].cat.ordered:
                    categories_counts = df[column].value_counts().reindex(
                        df[column].cat.categories, fill_value=0)
                else:
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

                    # Convert categorical types to numeric codes for Spearman's correlation
                    # cat.codes returns -1 for NA; replace with np.nan then mask.
                    def _to_float_codes(series):
                        codes = series.astype('category').cat.codes.to_numpy(dtype=float)
                        codes[codes == -1] = np.nan
                        return codes

                    arr_one = _to_float_codes(df[column_one])
                    arr_two = _to_float_codes(df[column_two])
                    mask = ~(np.isnan(arr_one) | np.isnan(arr_two))

                    # Calculate Spearman rank correlation
                    if mask.sum() < 2:
                        spearman_corr = 0.0
                    else:
                        spearman_corr, _ = ss.spearmanr(arr_one[mask], arr_two[mask])
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
            filename = os.path.join(report_dir, out_html)
            with open(filename, 'w') as f:
                f.write(html)

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

                if isinstance(df[i].dtype, pd.CategoricalDtype):
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

        fname = out_html

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

        x_labels = [str(v) for v in grp.index]
        plt.figure(figsize=(16, 4))
        a = sns.barplot(x=x_labels, y=grp.values,
                        order=x_labels,
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
    def prepare(df: pandas.DataFrame = None, auto_data_prep='internal', opts: dict = None, ):
        """
        Prepare a categorical dataset -- tries to convert ordinal values also in strings
        to ordinal variable.

        E.g. Values 'Under 12', '13-18', '19-25', ... , 'Over 75' are sorted correctly
        E.g.2 : values like 0,1,2,...,9,10,11,>=12 are also sorted correctly.

        :param df: DataFrame to prepare.
        :param auto_data_prep: Preparation engine to use.  Currently there
            are two engines supported - internal one and CleverMiner.
            Use ``'CLM'`` for CleverMiner and any other value for internal.
        :param opts: If CLM engine is used, these options are passed
            to CleverMiner as is.

        :returns: A new DataFrame with eligible columns converted to ordered
            ``pandas.CategoricalDtype``.  The input DataFrame is not modified.

        :raises: No exceptions are raised; columns that cannot be converted are
            returned as-is.

        .. note::
            CleverMiner >= 1.0.7 is required for CLM engine conversion.  If
            an older version is  installed the original DataFrame is returned unchanged.
        """
        #currently we are moving CleverMiner's data preparation to here, internal processing keeping as default
        #CleverMiner's data preparation is kept for compatibility
        
        my_df = df
        opts2 = opts if opts is not None else {}
        #prevent changing original df
        opts2['keep_df'] = True
        if auto_data_prep=='CLM':
            print("INFO: Using CleverMiner to prepare dataset")
            clm = cleverminer(df=my_df, opts=opts2)
            clm.print_data_definition()
            if cleverminer.version_string < '1.0.7':
                return my_df
            return clm.df
        else:
            print("INFO: Using INTERNAL AUTO PREPARATION")
            pandas_cat._automatic_data_conversions(df)
            for col in df.select_dtypes(exclude=['category']).columns:
                df[col] = df[col].apply(str)
            try:
                unique_counts = pd.DataFrame.from_records([(col, df[col].nunique()) for col in df.columns],
                                                          columns=['Column_Name', 'Num_Unique']).sort_values(
                    by=['Num_Unique'])
            except:
                print(
                    "Error in input data, probably unsupported data type. Will try to scan for column with unsupported type.")
                colname = ""
                try:
                    for col in df.columns:
                        colname = col
                        print(f"...column {col} has {int(df[col].nunique())} values")
                except:
                    print(f"... detected : column {colname} has unsupported type: {type(df[col])}.")
                    exit(1)
                print(
                    f"Error in data profiling - attribute with unsupported type not detected. Please profile attributes manually, only simple attributes are supported.")
                exit(1)
                          
            s = ""                          
            for column in df:
                s = f"Column {column}:"
                dfc = pd.get_dummies(df[column])
                for col2 in dfc:
                    s += f"{col2} "
                print(s)

            return df


    def _automatic_data_conversions(df):
        print("Automatically reordering numeric categories ...")
        verbosity = False
        for i in range(len(df.columns)):
            if verbosity:
                print(f"#{i}: {df.columns[i]} : {df.dtypes.iloc[i]}.")
            try:
                df[df.columns[i]] = df[df.columns[i]].astype(str).astype(float)
                if verbosity:
                    print(f"CONVERTED TO FLOATS #{i}: {df.columns[i]} : {df.dtypes.iloc[i]}.")
                lst2 = pd.unique(df[df.columns[i]])
                is_int = True
                for val in lst2:
                    if val % 1 != 0:
                        is_int = False
                if is_int:
                    df[df.columns[i]] = df[df.columns[i]].astype(int)
                    if verbosity:
                        print(f"CONVERTED TO INT #{i}: {df.columns[i]} : {df.dtypes.iloc[i]}.")
                lst3 = pd.unique(df[df.columns[i]])
                cat_type = CategoricalDtype(categories=sorted(lst3), ordered=True)
                df[df.columns[i]] = df[df.columns[i]].astype(cat_type)
                if verbosity:
                    print(f"CONVERTED TO CATEGORY #{i}: {df.columns[i]} : {df.dtypes.iloc[i]}.")

            except:
                if verbosity:
                    print("...cannot be converted to int")
                try:
                    values = df[df.columns[i]].unique()
                    if verbosity:
                        print(f"Values: {values}")
                    is_ok = True
                    valid_pairs = []
                    for val in values:
                        if pd.isna(val) or str(val).lower() in ('nan', 'na', 'none', ''):
                            continue
                        res = re.findall(r"-?\d+", str(val))
                        if len(res) > 0:
                            valid_pairs.append((int(res[0]), val))
                            #extracted.append(int(res[0]))
                        else:
                            is_ok = False
                    if is_ok and valid_pairs:
                        sorted_list = [v for _, v in sorted(valid_pairs, key=lambda x: x[0])]
                        cat_type = CategoricalDtype(categories=sorted_list, ordered=True)
                        df[df.columns[i]] = df[df.columns[i]].astype(cat_type)
                except:
                    if verbosity:
                        print("...cannot extract numbers from all categories")

        print("Automatically reordering numeric categories ...done")

            
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

            if hasattr(df[column], 'cat'):
                to_remove = [v for v in missing_values if v in df[column].cat.categories]
                if to_remove:
                    df[column] = df[column].cat.remove_categories(to_remove)
            else:
                df[column] = df[column].replace(missing_values, pd.NA)

        return df, detected_missing_values, replaced_counts
