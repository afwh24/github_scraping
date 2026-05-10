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
import dask.dataframe as dd
from config import tokenizer_model_path, input_dir, output_filtered_dir
from pathlib import Path
import pandas as pd

from nemo_curator.pipeline import Pipeline
from nemo_curator.stages.text.io.reader import JsonlReader
from nemo_curator.stages.text.io.writer import JsonlWriter

#ds = DocumentDataset.read_json("/workspace/alfred/github_scraping/data/test/january/output_2.jsonl")
months = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november","december"]
logfile_path = Path("/workspace/alfred/github_scraping/filter_error_logs.txt")


pandas_meta = pd.DataFrame({
    "repo_name": pd.Series(dtype="object"),
    "description": pd.Series(dtype="object"),
    "stars": pd.Series(dtype="Int64"),
    "file_count": pd.Series(dtype="Int64"),
    "size_kb": pd.Series(dtype="Int64"),
    "language": pd.Series(dtype="object"),
    "license": pd.Series(dtype="object"),
    "file_name": pd.Series(dtype="object"),
    "text": pd.Series(dtype="object"),

})

def loc_filter(dataset: DocumentDataset):
    loc_filter_chain = nc.Sequential([
    nc.ScoreFilter(
        NumberOfLinesOfCodeFilter(min_lines=5, max_lines=10000),
        text_field = "text",
        score_field= "loc"
    )
    ])

    return loc_filter_chain(dataset)


def alpha_filter(dataset: DocumentDataset):
    alpha_filter_chain = nc.Sequential([
        nc.ScoreFilter(
            AlphaFilter(min_alpha_ratio=0.25),
            text_field="text",
            score_field="alpha"
        )
    ])

    return alpha_filter_chain(dataset)


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
    


def HTML_filter(dataset: DocumentDataset):
    df = dataset.df
    html_df = df[df["language"].str.lower() == "html"]
    non_html_df = df[df["language"].str.lower() != "html"]


    html_boiler_filter = nc.ScoreFilter(HTMLBoilerplateFilter())

    #filter the html subset
    html_ds = DocumentDataset(html_df)
    html_filtered = html_boiler_filter(html_ds)

    #merge back html_filtered + non_html_df
    combined_df = dask_concat([html_filtered.df, non_html_df])

    return DocumentDataset(combined_df.repartition(npartitions=1))

def token_fertility_filter(dataset: DocumentDataset):
    tokenization_filter = nc.ScoreFilter(
        TokenizerFertilityFilter(
            path_to_tokenizer=tokenizer_model_path,
            min_char_to_token_ratio=2.5 #encode each token at least 2.5 chars on average
        )
    )

    return tokenization_filter(dataset)




