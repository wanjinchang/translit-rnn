import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import codecs

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--log',default='log')
parser.add_argument('--window',default=100, type=int)
parser.add_argument('--ymax',default=0, type=float)
args = parser.parse_args()


def smoothen(values, window = 10):
	new_values = []
	i = 0
	while i + window <= len(values) :
		new_values.append(sum(values[i:i+window])/window)
		i += 1
	if i < len(values):
		new_values.append(sum(values[i:])/(len(values) - i ) )
	return new_values
def is_float(s):
    try: 
        float(s)
        return True
    except ValueError:
        return False

log = codecs.open(args.log).readlines()
losses = [float(line.split()[-7]) for line in log if len(line.split()) >= 7 and is_float(line.split()[-7]) ]
val_losses = [float(line.split()[-1]) for line in log if line.split()[0] == 'validation' ]
losses = smoothen(losses, args.window)
X = [float(line.split()[1]) for line in log if len(line.split()) >= 2 and
        is_float(line.split()[1]) ][-len(losses):] # what the fuck :/ 
if args.ymax > 0:
	plt.ylim(0, args.ymax)

val_step = len(X) / len(val_losses)
if val_step * len(val_losses) >= len(X):
    val_step -= 1
val_x = [X[i] for i in range(val_step,len(X), val_step)]
plt.plot(val_x, val_losses)
plt.plot(X, losses)
plt.savefig(args.log + '.png')
