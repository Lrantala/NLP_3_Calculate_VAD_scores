import logging
import pandas as pd
import os
import sys
import csv
from timeit import default_timer as timer
import ast

SKIPPED_WORDS = ["None", "be"]
MILD_BOOSTER_WORDS = ["absolutely", "very", "really", "total", "totally", "especially", "definitely", "complete", "completely"]
STRONG_BOOSTER_WORDS = ["extremely", "fuckin", "fucking", "hugely", "incredibly", "overwhelmingly"]
NEGATION_WORDS = ["not"]
SKIPPED_WORDS = ["None", "be"]

def open_file(file, type):
    if type == "warriner":
        logging.debug("Entering open file warriner")
        raw_table = pd.read_csv(file, sep=',', encoding='utf-8')
    else:
        logging.debug("Entering open file pandas")
        raw_table = pd.read_csv(file, sep=';', encoding='utf-8')
    # This transforms the csv-strings back to a list
        raw_table["related"] = raw_table["related"].map(ast.literal_eval)
        raw_table["opinion"] = raw_table["opinion"].map(ast.literal_eval)
        raw_table["aspect"] = raw_table["aspect"].map(ast.literal_eval)
        raw_table["opinion_v"] = raw_table["opinion_v"].map(ast.literal_eval)
        raw_table["opinion_a"] = raw_table["opinion_a"].map(ast.literal_eval)
        raw_table["opinion_d"] = raw_table["opinion_d"].map(ast.literal_eval)
        raw_table["aspect_v"] = raw_table["aspect_v"].map(ast.literal_eval)
        raw_table["aspect_a"] = raw_table["aspect_a"].map(ast.literal_eval)
        raw_table["aspect_d"] = raw_table["aspect_d"].map(ast.literal_eval)
        raw_table["related_v"] = raw_table["related_v"].map(ast.literal_eval)
        raw_table["related_a"] = raw_table["related_a"].map(ast.literal_eval)
        raw_table["related_d"] = raw_table["related_d"].map(ast.literal_eval)
    return raw_table


def save_file(file, name):
    logging.debug("Entering writing pandas to file")
    try:
        filepath = "./save/"
        if not os.path.exists(filepath):
            os.makedirs(filepath)
        file.to_csv(filepath + name + ".csv", encoding='utf-8', sep=";", quoting=csv.QUOTE_NONNUMERIC)
        print("Saved file: %s%s%s" % (filepath, name, ".csv"))
    except IOError as exception:
        print("Couldn't save the file. Encountered an error: %s" % exception)
    logging.debug("Finished writing: " + name)


def read_folder_contents(path_to_files):
    filelist = os.listdir(path_to_files)
    return filelist


def booster_modification(booster_score, word_score):
    if word_score <= 5:
        word_score = word_score - booster_score
    elif word_score >= 5:
        word_score = word_score + booster_score
    return word_score


def negation_modification(negation_word, word_score):
    """This assigns opposite polarity to a sentence containing
    a negation modifier"""
    # With the presence of a single negation modifier, this step
    # is a bit redundant, but it will give easier time to expand it.
    if negation_word == "not":
        if word_score <= 5:
            word_score = float(format(word_score + (2 *(5 - word_score)), '.2f'))
        elif word_score >= 5:
            word_score = float(format(word_score - (2 *(word_score - 5)), '.2f'))
    return word_score

def calculate_vad_scores_as_mean_for_nouns(raw_df):
    logging.debug("Entering calculate new vad scores for noun phrases.")
    start = timer()
    df = raw_df
    new_aspect_scores = []
    lists = ["opin_new_v", "opin_new_a", "opin_new_d", "rela_new_v", "rela_new_a", "rela_new_d"]
    for i, phrase in enumerate(df["aspect"]):
        aspe_v = []
        aspe_a = []
        aspe_d = []
        for score in lists:
            if (score is "opin_new_v" or score is "rela_new_v"):
                aspe_v.append(df[score][i])
            elif (score is "opin_new_a" or score is "rela_new_a"):
                aspe_a.append(df[score][i])
            elif (score is "opin_new_d" or score is "rela_new_d"):
                aspe_d.append(df[score][i])
        new_aspect_scores.append((((sum(aspe_v))/len(aspe_v)), ((sum(aspe_a))/len(aspe_a)), ((sum(aspe_d))/len(aspe_d))))
    df_ascores = pd.DataFrame.from_records(new_aspect_scores, columns=("aspect_new_v", "aspect_new_a", "aspect_new_d"))
    df = pd.concat([df, df_ascores], axis=1, sort=False)
    end = timer()
    logging.debug("Time: %.2f seconds" % (end - start))
    return df

def calculate_vad_scores_as_mean_for_opinions_separately(raw_df):
    """This counts the mean of the opinionated and related scores.
    It counts them separately in case it is needed to have more emphasis
    on the opinionated word."""
    logging.debug("Entering calculate new vad scores for opinions/related words.")
    df = raw_df
    opin_scores = []
    related_scores = []
    start = timer()
    opinion_related = ["opinion", "related"]
    for i, phrase in enumerate(df["aspect"]):
        opin_v = []
        opin_a = []
        opin_d = []
        rela_v = []
        rela_a = []
        rela_d = []
        for words in opinion_related:
            if len(df[words][i]) != 0:
                j = 0
                while j+1 < len(df[words][i]):
                    if df[words][i][j] in MILD_BOOSTER_WORDS:
                        df[words + "_v"][i][j+1] = booster_modification(0.5, df[words + "_v"][i][j+1])
                        df[words + "_a"][i][j+1] = booster_modification(0.5, df[words + "_a"][i][j+1])
                        df[words + "_d"][i][j+1] = booster_modification(0.5, df[words + "_d"][i][j+1])
                        # Dangerous. Pops out a value. Works, but can mess things up royally.
                        # df[words + "_v"][i].pop(j)
                    elif df[words][i][j] in STRONG_BOOSTER_WORDS:
                        df[words + "_v"][i][j+1] = booster_modification(1, df[words + "_v"][i][j+1])
                        df[words + "_a"][i][j+1] = booster_modification(1, df[words + "_a"][i][j+1])
                        df[words + "_d"][i][j+1] = booster_modification(1, df[words + "_d"][i][j+1])
                    elif df[words][i][j] in NEGATION_WORDS:
                        df[words + "_v"][i][j+1] = negation_modification(df[words][i][j], df[words + "_v"][i][j+1])
                        df[words + "_a"][i][j+1] = negation_modification(df[words][i][j], df[words + "_a"][i][j+1])
                        df[words + "_d"][i][j+1] = negation_modification(df[words][i][j], df[words + "_d"][i][j+1])
                    j += 1
                if words == "opinion":
                    k = 0
                    while k < len(df[words][i]):
                        if (df[words][i][k] not in MILD_BOOSTER_WORDS + STRONG_BOOSTER_WORDS + NEGATION_WORDS + SKIPPED_WORDS):
                            opin_v.append(df[words + "_v"][i][k])
                            opin_a.append(df[words + "_a"][i][k])
                            opin_d.append(df[words + "_d"][i][k])
                        k+=1
                else:
                    k = 0
                    while k < len(df[words][i]):
                        if (df[words][i][k] not in MILD_BOOSTER_WORDS + STRONG_BOOSTER_WORDS + NEGATION_WORDS + SKIPPED_WORDS):
                            rela_v.append(df[words + "_v"][i][k])
                            rela_a.append(df[words + "_a"][i][k])
                            rela_d.append(df[words + "_d"][i][k])
                        k+=1
        #Error here. This counts means for opinions and related separately. They should be combined.
        if len(opin_v) != 0:
            new_ov = float(format(sum(opin_v)/len(opin_v), '.2f'))
            new_oa = float(format(sum(opin_a) / len(opin_a), '.2f'))
            new_od = float(format(sum(opin_d) / len(opin_d), '.2f'))
            opin_scores.append((new_ov, new_oa, new_od))
        if len(opin_v) == 0:
            opin_scores.append((0, 0, 0))
        if len(rela_v) != 0:
            new_rv = float(format(sum(rela_v)/len(rela_v), '.2f'))
            new_ra = float(format(sum(rela_a) / len(rela_a), '.2f'))
            new_rd = float(format(sum(rela_d) / len(rela_d), '.2f'))
            related_scores.append((new_rv, new_ra, new_rd))
        if len(rela_v) == 0:
            related_scores.append((0, 0, 0))

    df_oscores = pd.DataFrame.from_records(opin_scores, columns=("opin_new_v", "opin_new_a", "opin_new_d"))
    df_rscores = pd.DataFrame.from_records(related_scores, columns=("rela_new_v", "rela_new_a", "rela_new_d"))
    df = pd.concat([df, df_oscores], axis=1, sort=False)
    df = pd.concat([df, df_rscores], axis=1, sort=False)
    end = timer()
    logging.debug("Time: %.2f seconds" % (end - start))
    return df


def calculate_vad_scores_1_as_mean_for_aspects(raw_df):
    """This counts the aspect score as the mean of the opinionated and related scores.
    It takes into account the base noun scores."""
    logging.debug("Entering calculate new vad scores 1 for aspects.")
    df = raw_df
    opin_scores = []
    start = timer()
    opinion_related = ["opinion", "related", "aspect"]
    for i, phrase in enumerate(df["aspect"]):
        opin_v = []
        opin_a = []
        opin_d = []
        for words in opinion_related:
            if len(df[words][i]) != 0:
                j = 0
                while j+1 < len(df[words][i]):
                    if df[words][i][j] in MILD_BOOSTER_WORDS:
                        df[words + "_v"][i][j+1] = booster_modification(0.5, df[words + "_v"][i][j+1])
                        df[words + "_a"][i][j+1] = booster_modification(0.5, df[words + "_a"][i][j+1])
                        df[words + "_d"][i][j+1] = booster_modification(0.5, df[words + "_d"][i][j+1])
                        # Dangerous. Pops out a value. Works, but can mess things up royally.
                        # df[words + "_v"][i].pop(j)
                    elif df[words][i][j] in STRONG_BOOSTER_WORDS:
                        df[words + "_v"][i][j+1] = booster_modification(1, df[words + "_v"][i][j+1])
                        df[words + "_a"][i][j+1] = booster_modification(1, df[words + "_a"][i][j+1])
                        df[words + "_d"][i][j+1] = booster_modification(1, df[words + "_d"][i][j+1])
                    elif df[words][i][j] in NEGATION_WORDS:
                        df[words + "_v"][i][j+1] = negation_modification(df[words][i][j], df[words + "_v"][i][j+1])
                        df[words + "_a"][i][j+1] = negation_modification(df[words][i][j], df[words + "_a"][i][j+1])
                        df[words + "_d"][i][j+1] = negation_modification(df[words][i][j], df[words + "_d"][i][j+1])
                    j += 1
                k = 0
                while k < len(df[words][i]):
                    if (df[words][i][k] not in MILD_BOOSTER_WORDS + STRONG_BOOSTER_WORDS + NEGATION_WORDS + SKIPPED_WORDS):
                        opin_v.append(df[words + "_v"][i][k])
                        opin_a.append(df[words + "_a"][i][k])
                        opin_d.append(df[words + "_d"][i][k])
                    k+=1
        if len(opin_v) != 0:
            new_ov = float(format(sum(opin_v)/len(opin_v), '.2f'))
            new_oa = float(format(sum(opin_a) / len(opin_a), '.2f'))
            new_od = float(format(sum(opin_d) / len(opin_d), '.2f'))
            opin_scores.append((new_ov, new_oa, new_od))
        if len(opin_v) == 0:
            opin_scores.append((0, 0, 0))

    df_ascores = pd.DataFrame.from_records(opin_scores, columns=("aspect_new_v", "aspect_new_a", "aspect_new_d"))
    df = pd.concat([df, df_ascores], axis=1, sort=False)
    end = timer()
    logging.debug("Time: %.2f seconds" % (end - start))
    return df


def calculate_vad_scores_2_as_mean_for_aspects(raw_df):
    """This counts the aspect score as the mean of the opinionated and related scores.
    It does not take into account the base noun scores."""
    logging.debug("Entering calculate new vad scores 1 for aspects.")
    df = raw_df
    opin_scores = []
    start = timer()
    opinion_related = ["opinion", "related"]
    for i, phrase in enumerate(df["aspect"]):
        opin_v = []
        opin_a = []
        opin_d = []
        for words in opinion_related:
            if len(df[words][i]) != 0:
                j = 0
                while j+1 < len(df[words][i]):
                    if df[words][i][j] in MILD_BOOSTER_WORDS:
                        df[words + "_v"][i][j+1] = booster_modification(0.5, df[words + "_v"][i][j+1])
                        df[words + "_a"][i][j+1] = booster_modification(0.5, df[words + "_a"][i][j+1])
                        df[words + "_d"][i][j+1] = booster_modification(0.5, df[words + "_d"][i][j+1])
                        # Dangerous. Pops out a value. Works, but can mess things up royally.
                        # df[words + "_v"][i].pop(j)
                    elif df[words][i][j] in STRONG_BOOSTER_WORDS:
                        df[words + "_v"][i][j+1] = booster_modification(1, df[words + "_v"][i][j+1])
                        df[words + "_a"][i][j+1] = booster_modification(1, df[words + "_a"][i][j+1])
                        df[words + "_d"][i][j+1] = booster_modification(1, df[words + "_d"][i][j+1])
                    elif df[words][i][j] in NEGATION_WORDS:
                        df[words + "_v"][i][j+1] = negation_modification(df[words][i][j], df[words + "_v"][i][j+1])
                        df[words + "_a"][i][j+1] = negation_modification(df[words][i][j], df[words + "_a"][i][j+1])
                        df[words + "_d"][i][j+1] = negation_modification(df[words][i][j], df[words + "_d"][i][j+1])
                    j += 1
                k = 0
                while k < len(df[words][i]):
                    if (df[words][i][k] not in MILD_BOOSTER_WORDS + STRONG_BOOSTER_WORDS + NEGATION_WORDS + SKIPPED_WORDS):
                        opin_v.append(df[words + "_v"][i][k])
                        opin_a.append(df[words + "_a"][i][k])
                        opin_d.append(df[words + "_d"][i][k])
                    k+=1
        if len(opin_v) != 0:
            new_ov = float(format(sum(opin_v)/len(opin_v), '.2f'))
            new_oa = float(format(sum(opin_a) / len(opin_a), '.2f'))
            new_od = float(format(sum(opin_d) / len(opin_d), '.2f'))
            opin_scores.append((new_ov, new_oa, new_od))
        if len(opin_v) == 0:
            opin_scores.append((0, 0, 0))

    df_ascores = pd.DataFrame.from_records(opin_scores, columns=("aspect_new_v", "aspect_new_a", "aspect_new_d"))
    df = pd.concat([df, df_ascores], axis=1, sort=False)
    end = timer()
    logging.debug("Time: %.2f seconds" % (end - start))
    return df

def return_sys_arguments(args):
    if len(args) == 2:
        return args[1]
    else:
        return None


def main(df_part, name):
    df_vad_scores = calculate_vad_scores_1_as_mean_for_aspects(df_part)
    # df_vad_scores = calculate_vad_scores_as_mean_for_opinions(df_part)
    # df_vad_scores = calculate_vad_scores_as_mean_for_nouns(df_vad_scores)
    save_file(df_vad_scores, name + "_CALCULATED_R")
    # result = pd.concat([df_vad_scores, new_df], axis=1, sort=False)
    # result = separate_individual_words(result, True)

if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

    argument = return_sys_arguments(sys.argv)
    if argument is None:
        print("You didn't give an argument")
    elif os.path.isdir(argument):
        files = read_folder_contents(argument)
        print("Gave a folder: %s, that has %s files." % (argument, str(len(files))))
        x = 0
        for f in files:
            x += 1
            df = open_file(argument + "/" + f, "pandas")
            name = os.path.splitext(f)[0]
            print("Opened file: %s" % name)
            main(df, name)

    elif os.path.isfile(argument):
        df = open_file(argument, "pandas")
        name = os.path.splitext(argument)[0]
        main(df, name)

    else:
        print("You didn't give a file or folder as your argument.")