import sys
sys.path.append('/media/angelo/WorkData/git/VITAMIN')
from vitamin_model_checker.model_checker_interface.explicit import RBATL, RABATL
from vitamin_model_checker.utils.generators import RBCGS_generator, RABCGS_generator
import time


def run_experiments(num_states_min, num_states_max, num_resources_min, num_resources_max, bound, repetitions):
    with open('results.csv', 'w') as file:
        file.write('# States; # Resources; RBATL time [sec]; RABATL time [sec]\n')    
    for state in range(num_states_min, num_states_max+1, 10):
        for resource in range(num_resources_min, num_resources_max+1):
            phi = '(<1,2><{res}>F p)'.format(res=','.join([str(bound) for _ in range(0, resource)]))
            avg_rbtime = 0
            avg_rabtime = 0
            with open('results.csv', 'a') as file:
                file.write(str(state) + ';' + str(resource) + ';')
            for _ in range(0, repetitions):
                RBCGS_generator.generate_random_model_file(state, resource, 'tmp.txt')
                start = time.time()
                RBATL.model_checking(phi, 'tmp.txt')
                end = time.time()
                avg_rbtime += end-start
                RABCGS_generator.generate_random_model_file(state, resource, 'tmp.txt')
                start = time.time()
                RABATL.model_checking(phi, 'tmp.txt')
                end = time.time()
                avg_rabtime += end-start
            avg_rbtime = avg_rbtime / repetitions
            avg_rbtime = avg_rabtime / repetitions
            with open('results.csv', 'a') as file:
                file.write(str(avg_rbtime) + '; ' + str(avg_rabtime) + '\n')

if __name__ == "__main__":
    num_states_min = max(int(sys.argv[1]), 1)
    num_states_max = max(int(sys.argv[2]), 1)
    num_resources_min = max(int(sys.argv[3]), 1)
    num_resources_max = max(int(sys.argv[4]), 1)
    bound = max(int(sys.argv[5]), 1)
    repetitions = max(int(sys.argv[6]), 1)
    run_experiments(num_states_min, num_states_max, num_resources_min, num_resources_max, bound, repetitions)


