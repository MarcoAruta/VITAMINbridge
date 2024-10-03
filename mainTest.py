import time

# from vitamin_model_checker.model_checker_interface.explicit import RBATL
# start = time.time()
# result = RBATL.model_checking('<1><0,0>F(oc && rm && <1><0,0>F((pl || pr) && <1><0,0>F(oc && rm)))', './examples/RBATL/rover.txt')
# end = time.time()
# print('phi1')
# print(result)
# print('TIME:', end-start, 'seconds')
# start = time.time()
# result = RBATL.model_checking('<1,2><5,1>F(oc && rm && <1><0,0>F((pl || pr) && <1><0,0>F(oc && rm)))', './examples/RBATL/rover.txt')
# end = time.time()
# print('phi2')
# print(result)
# print('TIME:', end-start, 'seconds')
# start = time.time()
# result = RBATL.model_checking('<1,2><2,2>F(oc && rm && <1><0,0>F((pl || pr) && <1><0,0>F(oc && rm)))', './examples/RBATL/rover.txt')
# end = time.time()
# print('phi2_rb')
# print(result)
# print('TIME:', end-start, 'seconds')
# del RBATL

from vitamin_model_checker.model_checker_interface.explicit.RABATL import RABATL
print(RABATL.model_checking('<1,2,3,4><4>F(p1 && q2 && s4 && r3)', 'tmp'))
# <1,2,3,4><10>F(p0 && q1 && q2 && r2 && p2 && p3)





# for i in range(2, 11):
#     print('N. of resources: ', i)
#     start = time.time()
#     result  = RABATL.model_checking('(<1,2><{res}>F p)'.format(res=','.join(['2']*i)), f'./examples/RABATL/sensor_network{i}.txt')
#     end = time.time()
#     # print(result)
#     print('TIME:', end-start, 'seconds')




# RB-ATL
# Resources: 1 energy, 1 memory 
# TIME: 0.006029605865478516 seconds
# Resources: 2 energy, 2 memory 
# TIME: 0.21443557739257812 seconds
# Resources: 3 energy, 3 memory 
# TIME: 7.137519121170044 seconds
# Resources: 4 energy, 4 memory 
# TIME: 261.43060302734375 seconds

# RAB-ATL
# Resources: 1 energy, 1 memory 
# TIME: 0.007246255874633789 seconds
# Resources: 2 energy, 2 memory 
# TIME: 0.19492864608764648 seconds
# Resources: 3 energy, 3 memory 
# TIME: 5.23409366607666 seconds
# Resources: 4 energy, 4 memory 
# TIME: 177.9505763053894 seconds



# start = time.time()
# result  = RBATL.model_checking('(<1,2><2,2,2,2,2,2,2,2,2,2>F p)', './examples/RBATL/sensor_network4.txt')
# end = time.time()
# print(result)
# print('TIME:', end-start, 'seconds')
# result  = RBATL.model_checking('(<1,2,3><2,2>F h)', './examples/RBATL/RBATL_model.txt')

# n = 10

# for energy in range(1, n):
#     # for memory in range(1, n):
#     print('Resource bound', energy)
#     # print('Memory resource bound', memory)
#     phi = f'(<1,2><{energy},{energy}>F p)'
#     start = time.time()
#     result  = RBATL.model_checking(phi, './examples/RBATL/sensor_network.txt')
#     print('RBATL')
#     # print(result)
#     print(f'TIME: {time.time()-start} seconds')
    
#     start = time.time()
#     result  = RABATL.model_checking(phi, './examples/RABATL/sensor_network.txt')
#     print('RABATL')
#     # print(result)
#     print(f'TIME: {time.time()-start} seconds')

    # result  = RABATL.model_checking(phi, './examples/RABATL/sensor_network_mod.txt')
    # print('RABATL mod')
    # print(result)
    # print(f'TIME: {time.time()-start} seconds')