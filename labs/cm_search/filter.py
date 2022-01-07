# function that returns a list of all distinct journals in result
# result is a list of items that match a previous search
def get_distinct_journals(result):
    journals = []
    for entry in result:
        if entry.journal not in journals:
            journals.append(entry.journal)
    return journals


# function that returns a list of all distinct languages in result
# result is a list of items that match a previous search
def get_distinct_languages(result):
    languages = []
    for entry in result:
        if entry.language not in languages:
            languages.append(entry.language)
    return languages


# function that returns a list of all distinct years items were issued in in result
# result is a list of items that match a previous search
    # might need changes to only get the year out of items with date of issue like '1919-01-01'
def get_distinct_years(result):
    years = []
    for entry in result:
        if entry.year not in years:
            years.append(entry.year)
    return years
