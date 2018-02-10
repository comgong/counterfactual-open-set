import sys
import numpy as np
import time
import whattimeisit


class TimeSeries:
    def __str__(self):
        return self.format_all()

    def __init__(self, title=None):
        self.series = {}
        self.predictions = {}
        self.start_time = time.time()
        self.last_printed_at = time.time()
        self.title = title

    def collect(self, name, value):
        if not self.series:
            self.start_time = time.time()
        if name not in self.series:
            self.series[name] = []
        self.series[name].append(convert_to_scalar(value))

    def collect_prediction(self, name, logits, ground_truth):
        if name not in self.predictions:
            self.predictions[name] = {'correct': 0, 'total': 0}
        _, pred_idx = logits.max(1)
        _, label_idx = ground_truth.max(1)
        correct = convert_to_scalar(sum(pred_idx == label_idx))
        self.predictions[name]['correct'] += correct
        self.predictions[name]['total'] += len(ground_truth)

    def print_every(self, n_sec=4):
        if time.time() - self.last_printed_at > n_sec:
            print(self.format_all())
            self.last_printed_at = time.time()

    def format_all(self):
        lines = ['']
        if self.title:
            lines.append(self.title)
        duration = time.time() - self.start_time
        lines.append("Collected {:.3f} sec ending {}".format(
            duration, whattimeisit()))
        lines.append("Max Rate {:.2f}/sec".format(self.get_rate()))
        lines.append("{:>32}{:>12}{:>14}".format('Name', 'Avg.', 'Last 10'))
        for name in sorted(self.series):
            values = np.array(self.series[name])
            name = shorten(name)
            lines.append("{:>32}:      {:.4f}      {:.4f}".format(
                name, values.mean(), values[-10:].mean()))
        if self.predictions:
            lines.append('Predictions:')
        for name, pred in self.predictions.items():
            acc = 100 * pred['correct'] / pred['total']
            name = shorten(name)
            lines.append('{:>32}:\t{:.2f}% ({}/{})'.format(
                name, acc, pred['correct'], pred['total']))
        lines.append('\n')
        text = '\n'.join(lines)
        # Cache the most recent printed text to a file
        open('.last_summary.log', 'w').write(text)
        return text

    def get_rate(self):
        return max([len(c) for c in self.series]) / (time.time() - self.start_time)

    def write_to_file(self):
        filename = 'timeseries.{}.npy'.format(int(time.time()))
        ts = np.array(self.series[0])
        ts.save(filename)
        sys.stderr.write('Wrote array shape {} to file {}\n'.format(ts.shape, filename))


# We assume x is a scalar.
# If x is not a scalar, that is a problem that we will fix right now.
def convert_to_scalar(x):
    if type(x).__name__ == 'FloatTensor':
        x = x.cpu()[0]
    elif type(x).__name__ == 'Variable':
        x = x.data.cpu()[0]
    try:
        return float(x)
    except:
        pass
    return 0

def shorten(words, maxlen=30):
    if len(words) > 27:
        words = words[:20] + '...' + words[-9:]
    return words
