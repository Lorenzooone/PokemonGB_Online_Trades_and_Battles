import os
import time
import traceback
import sys

# From: https://github.com/Squaresweets/TileWorldGBA
max_packet_size_mb = 0x40

def read_exact(receiver, num_bytes, max_retries=20):
    data = b''
    while len(data) < num_bytes and max_retries > 0:
        try:
            chunk = receiver(num_bytes - len(data))
        except:
            chunk = b''
        if chunk is None or len(chunk) == 0:
            max_retries -= 1
            continue
        data += bytes(chunk)
    return data

def read_all(receiver, debug=False):
    time.sleep(0.01)
    output = 0
    prev_len = 0
    while True:
        try:
            data = receiver()
            if len(data) == 0:
                break
            output <<= (8 * len(data))
            output |= int.from_bytes(data, byteorder='big')
            if len(data) < max_packet_size_mb:
                break
        except:
            #traceback.print_exc()
            #print("Unexpected exception: ", sys.exc_info()[0])
            break
    if debug:
        print("0x%02x " % output)
    return output

def multiboot(receiver, sender, list_sender, path, reconfigure_function, requires_read_after_write):

    def mb_read_exact(num_bytes, max_retries=20):
        data = b''
        while len(data) < num_bytes and max_retries > 0:
            try:
                chunk = receiver(num_bytes - len(data))
            except:
                chunk = b''
            if chunk is None or len(chunk) == 0:
                max_retries -= 1
                continue
            data += bytes(chunk)
        return data

    def mb_send(data):
        sender(data, 4)
        if requires_read_after_write:
            mb_read_exact(4)

    def mb_transfer(data):
        sender(data, 4)
        if requires_read_after_write:
            return int.from_bytes(mb_read_exact(4), byteorder='big')
        return read_all(receiver)

    content = 0
    print("Preparing data...")
    content = bytearray(open(path, 'rb').read())
    fsize = os.path.getsize(path)
    # Padding to avoid errors
    content = content.ljust(fsize + 64, b'\0')

    if fsize > 0x3FF40:
        print("File size error, max " + 0x3FF40 + " bytes")
        exit()
    
    fsize += 0xF
    fsize &= ~0xF

    sending_data = [0]*((fsize-0xC0)>>2)
    complete_sending_data = [0]*(fsize-0xC0)
    crcC = 0xC387
    for i in range(0xC0, fsize, 4):
        dat = int(content[i])
        dat |= int(content[i + 1]) << 8
        dat |= int(content[i + 2]) << 16
        dat |= int(content[i + 3]) << 24

        tmp = dat

        for b in range(32):
            bit = (crcC ^ tmp) & 1
            if bit == 0:
                crcC = (crcC >> 1) ^ 0
            else:
                crcC = (crcC >> 1) ^ 0xc37b
            tmp >>= 1
            
        dat = dat ^ (0xFE000000 - i) ^ 0x43202F2F
        sending_data[(i-0xC0)>>2] = dat & 0xFFFFFFFF
        
    print("Data preloaded...")
    
    read_all(receiver)
    reconfigure_function(36, 4, list_sender, receiver)

    recv = 0
    while True:
        recv = mb_transfer(0x6202)
        if (recv >> 16) == 0x7202:
            break
    print("Lets do this thing!")
    mb_send(0x6102)

    for i in range(96):
        out = (int(content[(i*2)])) + (int(content[(i*2)+1]) << 8)
        mb_send(out)

    mb_send(0x6200)
    mb_send(0x6200)
    mb_transfer(0x63D1)

    token = mb_transfer(0x63D1)
    if ((token >> 24) & 0xFF) != 0x73:
        print("Failed handshake!")
        return
    else:
        print("Handshake successful!")

    crcA = (token >> 16) & 0xFF
    seed = 0xFFFF00D1 | (crcA << 8)
    crcA = (crcA + 0xF) & 0xFF

    mb_transfer(0x6400 | crcA)

    token = mb_transfer((fsize - 0x190) // 4)
    crcB = (token >> 16) & 0xFF
    print(fsize)
    print("Sending data!")
    
    for i in range(len(sending_data)):
        seed = (seed * 0x6F646573 + 1) & 0xFFFFFFFF
        complete_sending_data[(i*4)] = ((sending_data[i] ^ seed)>>24) & 0xFF
        complete_sending_data[(i*4)+1] = ((sending_data[i] ^ seed)>>16) & 0xFF
        complete_sending_data[(i*4)+2] = ((sending_data[i] ^ seed)>>8) & 0xFF
        complete_sending_data[(i*4)+3] = ((sending_data[i] ^ seed)>>0) & 0xFF
        
    time_transfer = time.time()
    list_post_transfer_function = None
    if requires_read_after_write:
        list_post_transfer_function = mb_read_exact
    list_sender(complete_sending_data, chunk_size = max_packet_size_mb, post_transfer_function = list_post_transfer_function)
    time_transfer = time.time()-time_transfer
    print(time_transfer)
    
    print("Data sent")

    tmp = 0xFFFF0000 | (crcB << 8) | crcA

    for b in range(32):
        bit = (crcC ^ tmp) & 1
        if bit == 0:
            crcC = (crcC >> 1) ^ 0
        else:
            crcC = (crcC >> 1) ^ 0xc37b
        tmp >>= 1

    read_all(receiver)
    mb_send(0x0065)
    while True:
        recv = mb_transfer(0x0065)
        if ((recv >> 16) & 0xFFFF) == 0x0075:
            break

    mb_send(0x0066)
    mb_send(crcC & 0xFFFF)
    print("DONE!")
