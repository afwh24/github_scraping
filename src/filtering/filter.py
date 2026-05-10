import nemo_curator as nc
from nemo_curator.datasets import DocumentDataset
from nemo_curator.filters import (
    GeneralCommentToCodeFilter,
    NumberOfLinesOfCodeFilter,
    AlphaFilter,
    XMLHeaderFilter,
    HTMLBoilerplateFilter,
    TokenizerFertilityFilter
)
from dask.dataframe import concat as dask_concat
from config import tokenizer_model_path
from pathlib import Path


#Nemo-curator Line-Of-Code (LOC) filter
def loc_filter(dataset: DocumentDataset):
    loc_filter_chain = nc.Sequential([
    nc.ScoreFilter(
        NumberOfLinesOfCodeFilter(min_lines=5, max_lines=10000),
        text_field = "text",
        score_field= "loc"
    )
    ])

    return loc_filter_chain(dataset)

#Nemo-curator alphabet ratio filter
def alpha_filter(dataset: DocumentDataset):
    alpha_filter_chain = nc.Sequential([
        nc.ScoreFilter(
            AlphaFilter(min_alpha_ratio=0.25),
            text_field="text",
            score_field="alpha"
        )
    ])

    return alpha_filter_chain(dataset)

#Nemo-curator xml configuration file filter
def xml_filter(dataset: DocumentDataset):
    #convert back to DocumentDataset to perform filtering
    df = dataset.df
    xml_df = df[df["language"].str.lower() == "xml"]
    non_xml_df = df[df["language"].str.lower() != "xml"]

    xml_header_filter = nc.ScoreFilter(XMLHeaderFilter())

    #filter the xml df
    xml_ds = DocumentDataset(xml_df)
    xml_filtered = xml_header_filter(xml_ds)

    #merge back xml_filtered + non_xml_df
    combined_df = dask_concat([xml_filtered.df, non_xml_df])

    return DocumentDataset(combined_df.repartition(npartitions=1))

#Nemo-curator HTML boiler tag filter
def HTML_filter(dataset: DocumentDataset):
    df = dataset.df
    html_df = df[df["language"].str.lower() == "html"]
    non_html_df = df[df["language"].str.lower() != "html"]

    #newly added to ignore malformed html 
    bad_pat = r"(<!\[[^\w])|([\x00-\x08\x0B\x0C\x0E-\x1F])"
    s = html_df["text"].fillna("").astype("str")            # cuDF/pandas null-safe
    html_df = html_df[~s.str.contains(bad_pat, regex=True)] 
    #--------
    html_boiler_filter = nc.ScoreFilter(HTMLBoilerplateFilter())

    #filter the html subset
    html_ds = DocumentDataset(html_df)
    html_filtered = html_boiler_filter(html_ds)

    
    #merge back html_filtered + non_html_df
    combined_df = dask_concat([html_filtered.df, non_html_df])

    return DocumentDataset(combined_df.repartition(npartitions=1))

#Nemo-curator token fertility filter
def token_fertility_filter(dataset: DocumentDataset):
    tokenization_filter = nc.ScoreFilter(
        TokenizerFertilityFilter(
            path_to_tokenizer=tokenizer_model_path,
            min_char_to_token_ratio=2.5 #encode each token at least 2.5 chars on average
        )
    )

    return tokenization_filter(dataset)


def all_filters(dataset: DocumentDataset):
    loc_filtered_ds = loc_filter(dataset)
    loc_alpha_filtered_ds = alpha_filter(loc_filtered_ds)
    loc_alpha_xml_filtered_ds = xml_filter(loc_alpha_filtered_ds)
    loc_alpha_xml_html_filtered_ds = HTML_filter(loc_alpha_xml_filtered_ds)

    final_filtered_ds = token_fertility_filter(loc_alpha_xml_html_filtered_ds)

    return final_filtered_ds
