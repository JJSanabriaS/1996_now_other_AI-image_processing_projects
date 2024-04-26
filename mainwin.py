__author__ = 'Alexandre Rezende'
import time
import sys
import traceback
import os
from datetime import datetime

debug = True
run_phase_odean = False
run_phase_kaustia = True

# Para executar, abrir o Terminal
# Mudar para o pasta com cd
# Executar: python main.py

# Colocar o arquivo no mesmo diretorio do main.py
# Nome do arquivo com as cotacoes
shares_file_name = 'share_Negativo1.txt'
# Colocar a pasta na mesma pasta do main.py. Comecar o nome da pasta com ./
# Pasta com os resultados do experimento
inputs_dir = './output_negativo'
# IMPORTANTE o script sobrescreve qualquer arquivo com o mesmo nome na pasta
# Nome do arquivo de saida terminado em csv
output_file = 'odean.csv'
# IMPORTANTE o script sobrescreve qualquer arquivo com o mesmo nome na pasta
# Nome do arquivo de saida da fase 2 terminado em csv
output_file_phase2 = 'kaustia.csv'
# Numero de periodos (periodo final)
periods = 29
# Periodo inicial
starting_period = 4
# Dotacao inicial
starting_wealth = 10000
# Quantidade de ativos
assets = ['A', 'B', 'C', 'D', 'E', 'F']
# Intervalos de Rendimento
intervalos = [-70, -50, -30, -20, -10, -5, -3, 0, 3, 5, 10, 20, 30, 50, 70, 100]

# Para colocar propriedades, basta colocar uma linha comecando com %, o nome da propriedade
# e o valor, separado por Tab.
# Exemplo: %sexo	Masculino

def load_shares(shares_file_name):
    shares = []
    shares_file = open(shares_file_name, 'r')
    for share_line in shares_file:
        share = share_line.split('|')
        if share[0] == "Ativo": continue
        share[4] = share[4][0:-1]
        shares.append(share)
        if debug:
           print 'Cotacao: %r' % (share)
    return shares

def load_subjects(inputs_dir):
    subjects = []
    subjects_names = []
    subjects_metadata = []
    metadata_names = []
    starting_dir = os.getcwd()
    subject_files = os.listdir(inputs_dir)
    os.chdir(inputs_dir)
    for file in subject_files:
        if (file[0:6]=='output' and file[-3:] == 'txt'):
           subject_file = open(file, 'r')
           subject_operations = []
           subject_metadata = []
           for operation_line in subject_file:
              if operation_line[0] == '#':
                 break
              elif (operation_line[0:5] == 'Dados'):
                 subject_name = operation_line[9:-1]
                 subjects_names.append(subject_name)
                 if debug:
                    print "Nome do participante: %r " % (subject_name)
                 continue
              elif (operation_line[0:6] == 'TABELA' or operation_line[0:7] == 'PERIODO'):
                 continue
              elif (operation_line[0] == '%'):
                 operation = operation_line.split('\t')
                 if not(operation[0][1:] in metadata_names):
                    metadata_names.append(operation[0][1:])
                 subject_metadata.append(operation[1][:-1])
              else:
                 operation = operation_line.split('\t')
                 if (len(operation) == 5):
                    operation[4] = operation[4][:-1]
                    subject_operations.append(operation)
                 else:
                    print "Arquivo mal formado: %r" % (file)
           if debug:
              print "Operacoes do participante: %r " % (subject_operations)
           subjects.append(subject_operations)
           subjects_metadata.append(subject_metadata)
    os.chdir(starting_dir)
    return subjects_names, subjects, subjects_metadata, metadata_names

def get_period_operations(operations_list, period):
    result = []
    for i in operations_list:
        if (int(i[0]) == period):
            result.append(i)
    return result

def get_period_shares(shares_list, period):
    result = []
    for i in shares_list:
        if (int(i[4]) == period):
            result.append(i)
    return result

def process_subject(name, subject_operations, metadata, shares, start, end):
    current_holdings = []
    current_buys = []
    current_wealth = starting_wealth
    qty_transactions = 0
    total_return = 0
    realized_gains = 0
    realized_losses = 0
    potential_gains = 0
    potential_losses = 0
    realized_gains_percentage = 0
    realized_losses_percentage = 0
    disposition_effect = 0
    stocks_qty = []
    average_stocks = 0
    turnover = []
    average_turnover = 0
    period_shares = []
    average_holdings = []
    for i in range(start, end+1):
        if debug:
            print "Period: %r" % i
        period_operations = get_period_operations(subject_operations, i)
        period_shares = get_period_shares(shares, i)
        traded_wealth = 0
        traded_shares = []
        if debug:
            print "Operations: %r " % period_operations
            print "Shares: %r" % period_shares
        period_starting_wealth = current_wealth
        for i in current_buys:
           for j in period_shares:
              if i[2] == j[0]:
                 period_starting_wealth += int(i[3])*float(j[2])
        for operation in period_operations:
           if operation[1] == 'C':
               current_buys.append(operation)
               qty_transactions += 1
               traded_wealth += int(operation[3])*float(operation[4])
               current_wealth -= int(operation[3])*float(operation[4])
               traded_shares.append(operation[2])
           elif operation[1] == 'V':
               qty_transactions += 1
               traded_wealth += int(operation[3])*float(operation[4])
               current_wealth += int(operation[3])*float(operation[4])
               traded_shares.append(operation[2])
               weighted_sum = 0
               weighted_qty = 0
               sold_qty = int(operation[3])
               temp_current_buys = []
               if debug:
                  print "Sell opr: %r" % operation
                  print "Sold_qty: %r" % sold_qty
                  print "Current buys antes: %r " % current_buys
               for buy in current_buys:
                  qty = 0
                  if (buy[2] != operation[2] or sold_qty == 0):
                     temp_current_buys.append(buy)
                     continue
                  elif int(buy[3]) > sold_qty:
                     temp_current_buys.append([buy[0], buy[1], buy[2], int(buy[3]) - sold_qty, buy[4]])
                     qty = sold_qty
                     sold_qty = 0
                  elif int(buy[3]) == sold_qty:
                     qty = int(buy[3])
                     sold_qty = 0
                  elif int(buy[3]) < sold_qty:
                     sold_qty -= int(buy[3])
                     qty = int(buy[3])
                  weighted_sum += qty*float(buy[4])
                  weighted_qty += qty
               if debug:
                  print "Current buys depois: %r: " % temp_current_buys
               current_buys = temp_current_buys
               if weighted_qty == 0:
                  print "Venda a descoberto: %r" % operation
                  continue
               weighted_price = weighted_sum/weighted_qty
               sale_return = float(operation[4])/weighted_price
               if sale_return > 1:
                  realized_gains += 1
               elif sale_return < 1:
                  realized_losses += 1
               if debug:
                  print "Preco medio compra: {}".format(weighted_price),
                  print "Retorno da operacao: {}".format(sale_return - 1)
           else:
              print "Tipo de operacao nao reconhecido: %r" % operation
        turnover.append(traded_wealth/period_starting_wealth)
        current_holdings = []
        for i in current_buys:
           try:
              current_holdings.index(i[2])
           except:
              current_holdings.append(i[2])
        stocks_qty.append(len(current_holdings))
        for share in period_shares:
           weighted_sum = 0
           weighted_qty = 0
#           traded = False
#           for i in traded_shares:
#               if i == share[0]:
#                  traded = True
#           if traded:
#              continue
           for buy in current_buys:
              if (buy[2] == share[0]):
                  weighted_sum += int(buy[3])*float(buy[4])
                  weighted_qty += int(buy[3])
           if weighted_qty == 0:
              continue
           weighted_price = weighted_sum/weighted_qty
           sale_return = float(share[1])/weighted_price
           if sale_return > 1:
              potential_gains += 1
           elif sale_return < 1:
              potential_losses += 1
           if debug:
              print "Ativo: %r" % (share)
              print "Preco medio compra: %r" % (weighted_price),
              print "Retorno potencial: %r" % (sale_return - 1)
        period_holdings = []
        total_holdings = current_wealth
        for asset in assets:
           asset_price = 0.0
           asset_holdings = 0.0
           for quote in period_shares:
              if asset == quote[0]:
                 asset_price = int(quote[1])
           for buy in current_buys:
              if asset == buy[2]:
                 asset_holdings += int(buy[3])*asset_price
           total_holdings += asset_holdings
           period_holdings.append(asset_holdings)
        period_holdings.append(current_wealth)
        period_holdings_share = []
        for i in period_holdings:
            period_holdings_share.append(i/total_holdings * 100)
        average_holdings.append(period_holdings_share)
        if debug:
        	print "Period holdings: %r " % period_holdings_share
    ending_wealth = current_wealth
    for i in current_buys:
       for j in period_shares:
          if i[2] == j[0]:
             ending_wealth += int(i[3])*float(j[1])
    total_return = (ending_wealth/starting_wealth) - 1
    average_stocks = float(sum(stocks_qty))/max(len(stocks_qty),1)
    average_turnover = float(sum(turnover))/max(len(turnover),1)
    overall_holdings = average_holdings[0]
    for i in average_holdings[1:]:
       for j in range(0, len(i)):
          overall_holdings[j] += i[j]
    for i in range(0, len(overall_holdings)):
        overall_holdings[i] = overall_holdings[i]/(end-start+1)
    if debug:
       print "Overall holdings: %r " % overall_holdings
    result = [name]
    result.append(qty_transactions)
    result.append(total_return)
    result.append(realized_gains)
    result.append(realized_losses)
    result.append(potential_gains)
    result.append(potential_losses)
    if (realized_gains+potential_gains==0):
       realized_gains_percentage = 0
    else:
       realized_gains_percentage = (float(realized_gains)/(realized_gains+potential_gains))
    result.append(realized_gains_percentage)
    if (realized_losses+potential_losses==0):
       realized_losses_percentage = 0
    else:
       realized_losses_percentage = float(realized_losses)/(realized_losses+potential_losses)
    result.append(realized_losses_percentage)
    disposition_effect = realized_gains_percentage - realized_losses_percentage
    result.append(disposition_effect)
    result.append(average_stocks)
    result.append(average_turnover)
    result.extend(overall_holdings)
    for i in metadata:
       result.append(i)
    print "Resultado: %r " % result
    return result

def get_operation(operations_list, period, asset):
    result = []
    for i in operations_list:
        if (int(i[0]) == period and i[2] == asset):
            operation = [int(i[0]), i[1], i[2], int(i[3]), float(i[4])]
            result.append(operation)
    return result

def get_asset_price(shares_list, period, asset):
    for i in shares_list:
        if (int(i[4]) == period and i[0] == asset):
            return float(i[1])

def get_asset_max_price(shares_list, period, asset):
    max_price = 0.0
    for i in shares_list:
        if (int(i[4]) <= period and i[0] == asset):
            if float(i[1]) > max_price:
                max_price = float(i[1])
    return max_price

def get_asset_min_price(shares_list, period, asset):
    min_price = 10000000.0
    for i in shares_list:
        if (int(i[4]) <= period and i[0] == asset):
            if float(i[1]) < min_price:
                min_price = float(i[1])
    return min_price

def process_subject_phase2(code, name, subject_operations, metadata, shares, num_periods):
    result = []
    current_portfolio = []
    for i in assets:
        current_portfolio.append([0, 0, False])
    for i in range(1, num_periods+1):
        for j in assets:
            if debug:
                print "Period %r, Asset %r" % (i,j)
            current_result = [code, name, i, j]
            period_operation = get_operation(subject_operations, i, j)
            if (debug and len(period_operation)>1):
                print "More than one operation per period name: %r, operations: %r" % (name, period_operation)
            asset_price = get_asset_price(shares, i, j)
            # result variables
            sale = ''
            buy = ''
            if (current_portfolio[assets.index(j)][0] != 0):
                sale = '0'
                buy = '0'
            paper_result = ''
            paper_range = [0]*(len(intervalos)+1)
            capital_result = ''
            capital_range = [0]*(len(intervalos)+1)
            paper_result_max_price = ''
            paper_result_min_price = ''
            capital_result_max_price = ''
            capital_result_min_price = ''
            result_previous_period = ''
            consider_for_hold = True
            for operation in period_operation:
                if debug:
                    print "Operation: %r" % operation
                    print "Current portfolio pre: %r" % current_portfolio
                if (operation[1] == 'C'):
                    if (not current_portfolio[assets.index(j)][2]):
                        buy = '1'
                        consider_for_hold = False
                    elif (current_portfolio[assets.index(j)][0] != 0):
                        buy = '2'
                    else:
                        buy = '3'
                        consider_for_hold = False
                    current_portfolio[assets.index(j)][1] = (current_portfolio[assets.index(j)][0]*current_portfolio[assets.index(j)][1]+operation[3]*operation[4])/(current_portfolio[assets.index(j)][0]+operation[3])
                    current_portfolio[assets.index(j)][0] += operation[3]
                    current_portfolio[assets.index(j)][2] = True
                elif (operation[1] == 'V'):
                    sale = '1'
                    if (current_portfolio[assets.index(j)][0] == operation[3]):
                        consider_for_hold = False
                        current_portfolio[assets.index(j)][0] = 0
                    elif (current_portfolio[assets.index(j)][0] < operation[3]):
                        print "Venda a descoberto name: %r; operation: %r" % (name, operation)
                        consider_for_hold = False
                        if (current_portfolio[assets.index(j)][0] == 0):
                            continue
                        current_portfolio[assets.index(j)][0] = 0
                    else:
                        current_portfolio[assets.index(j)][0] -= operation[3]
                    capital_result = str((operation[4]/current_portfolio[assets.index(j)][1]-1)*100)
                    if (float(capital_result) <= float(intervalos[0])):
                        capital_range = [1]
                        for z in intervalos[1:]:
                            capital_range.append(0)
                        capital_range.append(0)
                    elif (float(capital_result) > float(intervalos[-1])):
                        capital_range = []
                        for z in intervalos:
                            capital_range.append(0)
                        capital_range.append(1)
                    else:
                        capital_range = [0]
                        for n in range(0, len(intervalos)-1):
                            if (float(capital_result) > float(intervalos[n]) and float(capital_result) <= float(intervalos[n+1])):
                                capital_range.append(1)
                            else:
                                capital_range.append(0)
                        capital_range.append(0)
                    capital_result_max_price = str((operation[4]/get_asset_max_price(shares, i, j)-1)*100)
                    capital_result_min_price = str((operation[4]/get_asset_min_price(shares, i, j)-1)*100)
                    result_previous_period = str((operation[4]/get_asset_price(shares, i-1, j)-1)*100)
                if debug:
                   print "Current portfolio pos: %r" % current_portfolio
            if (consider_for_hold and current_portfolio[assets.index(j)][0] > 0):
                paper_result = str((asset_price/current_portfolio[assets.index(j)][1]-1)*100)
                if (float(paper_result) <= float(intervalos[0])):
                    paper_range = [1]
                    for z in intervalos[1:]:
                        paper_range.append(0)
                    paper_range.append(0)
                elif (float(paper_result) > float(intervalos[-1])):
                    paper_range = []
                    for z in intervalos:
                        paper_range.append(0)
                    paper_range.append(1)
                else:
                    paper_range = [0]
                    for n in range(0, len(intervalos)-1):
                        if (float(paper_result) > float(intervalos[n]) and float(paper_result) <= float(intervalos[n+1])):
                            paper_range.append(1)
                        else:
                            paper_range.append(0)
                    paper_range.append(0)
                paper_result_max_price = str((current_portfolio[assets.index(j)][1]/get_asset_max_price(shares, i, j)-1)*100)
                paper_result_min_price = str((current_portfolio[assets.index(j)][1]/get_asset_min_price(shares, i, j)-1)*100)
            current_result.extend([sale, buy, paper_result])
            current_result.extend(paper_range)
            current_result.extend([capital_result])
            current_result.extend(capital_range)
            current_result.extend([paper_result_max_price, paper_result_min_price, capital_result_max_price, capital_result_min_price, result_previous_period])
            current_result.extend(metadata)
            if debug:
                print "Current result: %r" % current_result
            result.append(current_result)
    return result

def write_results_file(metadata_names, results, output_file, header):
    result_file = open(output_file, 'w')
    result_file.truncate()
    result_file.write(header)
    for result_item in results:
       result_str = ''
       for i in result_item:
          if (str(i)==""):
              result_str += "NaN"
          else:
              result_str += str(i)
          result_str += ';'
       result_file.write(result_str[:-1])
       result_file.write('\n')

def print_error(inst, msg):
    print "---- Erro ----"
    print "Erro: %r " % msg
    print type(inst)     # the exception instance
    print inst.args      # arguments stored in .args
    print inst
    print "Unexpected error:", sys.exc_info()
    traceback.print_tb(sys.exc_info()[2])
    print "---- Erro ----"
    return


try:
    shares = load_shares(shares_file_name)
    subject_names, subjects, subjects_metadata, metadata_names = load_subjects(inputs_dir)
    if (run_phase_odean):
        results = []
        for i in range(0, len(subject_names)):
            subject_result = process_subject(subject_names[i], subjects[i], subjects_metadata[i], shares, starting_period, periods)
            if debug:
                print "Resultado do %r : %r" % (subject_names[i], subject_result)
            results.append(subject_result)
        if debug:
            print "Resultados: %r" % results
        header = "Nome; Transacoes; Total Return; GR; PR; GNR; PNR; PGR; PPR; ED(Individual); Media ativos; Mean turnover; " + ";".join(assets) + "; Cash; " + ";".join(metadata_names) + "; \n"
        write_results_file(metadata_names, results, output_file, header)
    if (run_phase_kaustia):
        results = []
        for i in range(0, len(subject_names)):
            subject_result = process_subject_phase2(i+1, subject_names[i], subjects[i], subjects_metadata[i], shares, periods)
            if debug:
                print "Resultado fase 2 do %r : %r" % (subject_names[i], subject_result)
            results.extend(subject_result)
        if debug:
            print "Resultados Fase 2: %r" % results
        header = "PT; NPT; NP; AT; VD; CP; GPPP; " + str(intervalos)[1:-1].replace(",",";") + "; >" + str(intervalos[-1]) + "; GCPC; " + str(intervalos)[1:-1].replace(",",";") + "; >" + str(intervalos[-1]) + "; GPPMAX; GPPMIN; GPRMAX; GPRMIN; RPA; " + ";".join(metadata_names) + "; \n"
        write_results_file(metadata_names, results, output_file_phase2, header)
except Exception as inst:
   print_error(inst, "Erro")
