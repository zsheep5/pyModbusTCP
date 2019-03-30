import modbus_utils as mu
import modbus_client as mc 
import random as r
import db_access as db
import settings as sett

def test_write_profile ():
    _cl = mc.ModbusClient(sett.SERVER_IP_ADDRESS, sett.PORT)
    if not _cl.open():
        return False

    _counter = 0 
    print('write_profile')
    while _counter < 6:
        _cl.write_multiple_register_ascii(1000+(_counter*100), 'Barcode test 1')
        _cl.write_multiple_register_ascii(1020+(_counter*100), 'Test Part1')
        _cl.write_multiple_register_ascii(1037+(_counter*100), 'we are testing server logic')
        _cl.write_single_register(1067+(_counter*100), _counter+1)
        _cl.write_single_register(1068+(_counter*100), r.randrange(5))
        _cl.write_single_register(1069+(_counter*100), r.randrange(3))
        _cl.write_single_register(1070+(_counter*100), r.randrange(6000))
        _cl.write_single_register(1071+(_counter*100), r.randrange(2500))
        _cl.write_single_register(1072+(_counter*100), r.randrange(1000))
        _cl.write_single_register(1073+(_counter*100), r.randrange(1))
        _cl.write_single_register(1074+(_counter*100), r.randrange(0,45))
        _cl.write_single_register(1075+(_counter*100), r.randrange(45,120))
        _cl.write_single_register(1076+(_counter*100), r.randrange(0,500))
        _cl.write_multiple_register_ascii(1077+(_counter*100), 'testing instructions step %s'%(_counter))
        _counter = _counter + 1

    _cl.write_single_register(10, 1)
    _cl.write_single_coil(90, 1)
    print('end write')


test =db.create_con()
if db.create_tables(test) :
    test.close()
    print(test_write_profile())
else :  
    print ('failed on something')





