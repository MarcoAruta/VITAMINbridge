from vitamin_model_checker.model_checker_interface.explicit.NatATL.NatATL import model_checking


path = './examples/NatATL/exampleModel1.txt'
# formula = '<{1,3}, 2>Xh'
formula = '!(<{1,2}, 50>X(a and b) and <{1,2}, 50>Xc)'
# formula = '<{1,2}, 1>hUb'

#main function
model_checking(path, formula)


