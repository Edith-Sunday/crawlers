from openpyxl import load_workbook

def test_file(filename: str):
    wb = load_workbook('base.xlsx')
    # names = wb.sheetnames
    # print(names)
    # product_data = wb["Packages"]
    sheet = wb["Packages"]

    if sheet.max_column > 8:
        print('abort')
    else:
        print('safe')
    # length_indicator = []
#   find  way to remove the  first two columns for all the columns

    # for col in product_data.iter_cols(min_col=0, max_col=8):
    #     # length_indicator.append(col)
    #     print(col)

        # if not col.value:
            # continue
            # print(len(col.value))

test_file('base.xlsx')