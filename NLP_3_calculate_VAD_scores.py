import logging
import pandas as pd
import os
import sys
import csv
from timeit import default_timer as timer
import ast

SKIPPED_WORDS = ["None", "be"]


def open_file(file, type):
    if type == "warriner":
        logging.debug("Entering open file warriner")
        raw_table = pd.read_csv(file, sep=',', encoding='utf-8')
    else:
        logging.debug("Entering open file pandas")
        raw_table = pd.read_csv(file, sep=';', encoding='utf-8')
    # This transforms the csv-string back to a list
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


def calculate_vad_scores_for_phrases(raw_df):
    """This assigns the opinion words as the base score for every
    asoect and then modifies it by calculating the related words in it."""
    logging.debug("Entering calculate new vad scores")
    df = raw_df
    phrase_scores = []

    # aspect, opinion and related temp tables
    av = []
    aa = []
    ad = []
    ov = []
    oa = []
    od = []
    rv = []
    ra = []
    rd = []
    start = timer()
    for i, phrase in enumerate(df["aspect"]):
        temp_a = []
        temp_v = []
        temp_d = []
        if len(df["opinion"][i]) != 0:
            temp_v.extend(df["opinion_v"][i])
            temp_a.extend(df["opinion_a"][i])
            temp_d.extend(df["opinion_d"][i])

        if len(temp_v) != 0:
            new_v = float(format(sum(temp_v)/len(temp_v), '.2f'))
            new_a = float(format(sum(temp_a) / len(temp_a), '.2f'))
            new_d = float(format(sum(temp_d) / len(temp_d), '.2f'))
            phrase_scores.append((new_v, new_a, new_d))
    df_scores = pd.DataFrame.from_records(phrase_scores, columns=("new_v", "new_a", "new_d"))
    df = pd.concat([df, df_scores], axis=1, sort=False)
    #     for word, v, a, d in phrase:
    #         new_word.append(word)
    #         valence.append(v)
    #         arousal.append(a)
    #         dominance.append(d)
    #     for word, v, a, d in (new_adjectives[i]):
    #         if word not in SKIPPED_WORDS:
    #             if v < 4 or v > 6:
    #                 valence.append(v)
    #                 arousal.append(a)
    #                 dominance.append(d)
    #             elif a < 4 or a > 6:
    #                 valence.append(v)
    #                 arousal.append(a)
    #                 dominance.append(d)
    #             elif d < 4 or d > 6:
    #                 valence.append(v)
    #                 arousal.append(a)
    #                 dominance.append(d)
    #     new_string = ' '.join(new_word).lower()
    #     new_valence = float(format(sum(valence)/len(valence), '.2f'))
    #     new_arousal = float(format(sum(arousal)/len(arousal), '.2f'))
    #     new_dominance = float(format(sum(dominance)/len(dominance), '.2f'))
    #     original_scores.append(phrase)
    #     phrase_scores.append((new_string, str(new_valence), str(new_arousal), str(new_dominance)))
    # df_scores = pd.DataFrame.from_records(phrase_scores, columns=("clean_phrase", "valence", "arousal", "dominance"))
    # old_scores = pd.Series(original_scores)
    # df_scores["single_words"] = old_scores.values
    # end = timer()
    # logging.debug("Time: %.2f seconds" % (end - start))
    return df


def return_sys_arguments(args):
    if len(args) == 2:
        return args[1]
    else:
        return None


def main(df_part, name):
    df_vad_scores = calculate_vad_scores_for_phrases(df_part)
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