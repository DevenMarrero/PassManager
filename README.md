# PassManager

## Description
Python code for a sever-run password manager that can be accessed from anywhere. Supports multiple users and all passwords are encrypted.

This project was born out of neccesity as many of my personal accounts were being logged into by unknown people due to all my passwords being the same.
I wanted to make my passwords unique and needed a way to safely store them. Paying for a service to do that for me wasn't ideal so I made a program that can keep
all my passwords safely encrypted on my home computer while being accessed from anywhere.

## Installation
**Python Clone**

Install libraries using

`pip install Requirements.txt`

## Quick Lesson on Internet connections

Each device on your wifi is given an **internal** IP address so home devices can communicate. For example my PC's internal address is 10.0.0.40 and my phone is 10.0.0.41

Your router is connected to the internet using an **external** IP address and it acts as a gateway between the internet and your internal devices.
You can easily find your external IP address on a website called [portchecktool.com](https://www.portchecktool.com/) next to `Your Current Public IP Address is:`

A port forward is setup through your router and allows a device not on your network to directly connect to a device that is on the network as if they both were.
More on how to setup a port forward later.

## Setting up Server to be Local or Public

**Server Only Accessable on your Network (Local)**

The server will automatically use the local IP of the mchine it is running on.
The programm will ask you what port to run the server on and this can be any number between 1 and about 63000 but I use port 8050 as I can remember it and
as far as I know it is unused by other programms.

The server will then print a message similar to `[LISTENING] Server is listening on 10.0.0.40:8050` where 10.0.0.40:8050 = (IP Address):(Port)

When running Client.py for the first time it will create the file `Server.txt` which will look like this

```
(ENTER IP HERE) -IP
(ENTER PORT HERE) -Port
```

You need to then replace the fields with the IP address and port the server gave you
This options will be used automatically next time you start the Client so to change servers just edit the text file

**Server Accessable Anywhere (Public)**

This is very similar to the local setup however you will need to setup a port forward first, the instruction for that can be found below.

Once the port forward has been setup make sure the server is running on the forwarded port and that the fields in `Server.txt` are filled in as 

```
(Your wifi's external IPV4 address) -IP
(Server port) -Port
```

## Seting up a port forward

To setup a port forward you need to login to your routers gateway through your browser. You can find the gateway by opening a Windows Command-Prompt 
(press Start and search for 'cmd') and typing `ipconfig` into the prompt. In the results that come up find the Default Gateway.
```
Default Gateway . . . . . . . . . : fe80::461c:12ff:fe35:30c4%17
                                       10.0.0.1
```
Ignoring the first line of numbers my gateway is 10.0.0.1.

Copy and past your gateway into your browser's address bar and it should take you to a page similar to mine.
![](https://user-images.githubusercontent.com/70239160/99212206-5a0c0880-277f-11eb-871f-4c16effde361.png)

If you have not changed them your login credentials should be on a sticker on the underside of your router. The defualt username is usually 'admin' and passwords will 
usually be '(blank)', 'password', 'admin', or '1234'.

Once you have logged in find the Port Forwarding option which will usually be under Advanced. The exact layout and wording may change between ISP's.
Next you will want to enter a name for the device you are forwarding to and then under `Protocal` Select "TCP/UDP" or "Both", finally enter the internal IP address 
of the device the server is running on (IP the server prints out in the [Listening] message).

After aplying the changes start Server.Py on the forwarded port and head back to [portchecktool.com](https://www.portchecktool.com/) and check if your port is working. 
If it is you are good to go but if not try forwarding a different port or searching for tutorials for your specific ISP.

## Using Server

Once you have connected to the server as a client you are greeted with a welcome menu
```
-LOGIN MENU-
1 - Login
2 - Create new User
:
```

You navigate through menus by typing the number next to the option you would like.
