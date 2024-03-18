from pycomm.ab_comm.clx import Driver as ClxDriver
import logging

from time import sleep


if __name__ == '__main__':

    logging.basicConfig(
        filename="ClxDriver.log",
        format="%(levelname)-10s %(asctime)s %(message)s",
        level=logging.DEBUG
    )
    c = ClxDriver()

    print c['port']
    print c.__version__


    if c.open('192.168.12.5'):
        while 1:
            try:
                # print(c.read_tag(['ControlWord']))
                # print(c.read_tag(['parts', 'ControlWord', 'Counts']))
                c.forward_open()
                # print(c.write_tag('caseGtinText', 1, 'INT'))
                # print(c.write_tag(('bag_value', 12994, 'DINT')))
                # print(c.write_tag(('bag_value', 12994, 'DINT')))
                # print c.write_string('result', 'manoj','STRING')
                c.write_string('result', 'prathap')
                c.read_string('result')

                # reset tha array to all 0
                w_array = []
                for i in xrange(1750):
                    w_array.append(0)
                c.write_array("TotalCount", w_array, "SINT")

                c.close()
                # print(c.write_tag([('Result', 1996, 'INT')]))
                # print(c.write_tag([('Counts', -26, 'INT'), ('ControlWord', -30, 'DINT'), ('parts', 31, 'DINT')]))
                sleep(1)
            except Exception as e:
                c.close()
                print e
                pass

        # To read an array
        r_array = c.read_array("TotalCount", 1750)
        for tag in r_array:
            print (tag)

        c.close()
