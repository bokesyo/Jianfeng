
def write_mln_files(fact_list, predicate_list, function_list, nen_per, nen_org, nen_loc, db_path, mln_path):

    # Write Knowledge Base to files
    with open(db_path, mode='w') as file:
        file.write("")

    with open(db_path, mode='a') as file:
        for i in fact_list:
            file.write(i.body)
            file.write('\n')  # 换行

    # Write MLN

    with open(mln_path, mode='w') as file:
        file.write("")

    with open(mln_path, mode='a') as file:
        if function_list:
            for i in function_list:
                file.write(i)
                file.write('\n')  # 换行

        file.write('\n')

        if nen_per:
            string = 'person = {' + nen_per + '}'
            file.write(string)
            file.write('\n')  # 换行

        if nen_org:
            string = 'organization = {' + nen_org + '}'
            file.write(string)
            file.write('\n')  # 换行

        if nen_loc:
            string = 'location = {' + nen_loc + '}'
            file.write(string)
            file.write('\n')  # 换行

        file.write('\n')

        if predicate_list:
            for i in predicate_list:
                string = '1 ' + i.body
                file.write(string)
                file.write('\n')  # 换行


