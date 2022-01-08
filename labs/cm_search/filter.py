# function that returns a list of all distinct journals in result
# result is a list of items that match a previous search
def get_distinct_journals(result, checked_items):
    unchecked_journals = []
    for formatted_doc in result:
        if formatted_doc["j_title"] not in unchecked_journals and formatted_doc["j_title"] not in checked_items:
            unchecked_journals.append(formatted_doc["j_title"])
    journals = {
        "checked": checked_items,
        "unchecked": unchecked_journals
        }
    return journals


# function that returns a list of all distinct languages in result
# result is a list of items that match a previous search
def get_distinct_languages(result):
    languages = []
    for formatted_doc in result:
        if formatted_doc["lang"] not in languages:
            languages.append(formatted_doc["lang"])
    return languages


# function that returns a list of all distinct years items were issued in in result
# result is a list of items that match a previous search
    # works only for dates of issue like '1919-01-01' -> gets '1919'
def get_distinct_years(result):
    years = []
    for formatted_doc in result:
        if formatted_doc["dateIssued"][:4] not in years:
            years.append(formatted_doc["dateIssued"][:4])
    return years
