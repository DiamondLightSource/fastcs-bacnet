[![CI](https://github.com/DiamondLightSource/fastcs-bacnet/actions/workflows/ci.yml/badge.svg)](https://github.com/DiamondLightSource/fastcs-bacnet/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/fastcs-bacnet.svg)](https://pypi.org/project/fastcs-bacnet)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)

# fastcs_bacnet

The purpose of this package is to replace Diamond Light Source's current BMS system.

The purpose of both of these is to monitor certain properties of devices on the BACnet network and write them to an IOC.
The program uses BAC0 and BacPyPes3 to read data off of the BACnet network and FastCS to create the IOC.
Deployment and services repositorys for kubernetes can be found in the table below.

## Process

The fastcs bacnet program is run in 4 steps:
- Parsing the EDE file
- Creating the BacnetClient instance
- Creating the BacnetController instance
- Starting FastCS
All files relevant to this are in `src/fastcs_bacnet/core/`

### Parsing the EDE File

All done in the parse_ede method in `core/ede_parser.py`. This takes in an EDE file and a bms.ini file and returns a list of objects to subscribe to as well as what thier respective PVs should be called. The PV names are important as this is a non-trivial mapping (many symbols in BACnet object names are not valid for PV names). Most of the PV naming code is from the dls_bms project, the original repository can be found here: https://github.com/DiamondLightSource/dls_bms (for now).

EDE files are spreadsheets (.xls or .xlsx) provided by the IFM team to specify which objects on the BACnet network they want to subscribe to.
The bms.ini file specifies naming prefixes and protocols for each BACnet device. It is critical to the process of deciding EPICS PV names. 

### BacnetClient & BacnetController

The BacnetClient is the root node of a tree structure that holds and manages the BACnet subscriptions. More information on this is given in the structure section. This tree is constructed from the list of BACnet objects to subscribe to.
The BacnetController is the root node of an equivalent tree structure. However, this one holds and manages the EPCICS PVs (using FastCs). This tree is created by copying the structure of the BACnet tree. This happens on initialisation of the BacnetController instance using the BacnetClient that is passed in as an argument. There is also more information on this in the Structure section.
This structure allow clear separation of the BACnet and FastCS sides of the program.

### Starting FastCS

Once the FastCS controller has been created the FastCS application can be started. This is when the IOC will be started.

IMPORTANT NOTE: Although the BACnet subscription handling is set up on creation of the BacnetClient object, BACnet subscription requests are sent out at THIS stage (more specifically in post_initialise method of the BacnetController).

It is very important the following events occur in the correct order for every subscription:
1. Creation of the ObjectSubscription CallbackHolder (in BacnetClient intialisation)
2. Making the BACnet updates update their respective FastCS attribute (in BacnetController intialisation)
3. Starting the BACnet subscriptions (is BacnetController post_initialise method)

1 is essential for 2 because a CallbackHolder is what allows functions to be called when an update is recieved. If 3 is done before 2 then the initial subscription response will not update the attribute (and therefore the PV). This will leave the PV with an uninitialised value until another update is recieved from the device. Some objects update very rarely so this is not ideal.

## Structure

When the program is run 2 trees are created: one for handling BACnet subscriptions and one for updating FastCS PVs. To create the BACnet tree a list of SubscriptionIDs is used. The FastCS tree is created from the BACnet tree.

### SubscriptionID

SubscriptionID is a dataclass used to identify a specific object on a specific BACnet device. It comes in 2 halves: An IPv4SocketAddress to identify a device and an ObjectIdentifier to identify an object on that device.
IPv4SocketAddress is also a dataclass. It contains fields for an IP address and port number (this is for testing purposes, BACnet devices always use port number 47808 for communication). It also has a field for the device instance number but this is for debugging purposes.
ObjectIdentifier is also a dataclass with fields for object type and object instance number.

### BACnet Tree

The root node of the BACnet tree is the BacnetClient instance. This recieves a list of SubscriptionIDs in its constructor to create the tree. For each unique device (IPv4SocketAddress) in this list it creates a DeviceSubscription instance. 
The DeviceSubscription class handles listening for Iam requests from its device and rate limiting requests sent to the device. However, its main purpose is to store all ObjectSubscription instances for the specific device.
ObjectSubscriptions represent the subscription to a specific object on a BACnet device. They have a CallbackHolder instance to hold any callback procedures to run when an update is recieved. They also allow for setting a callback for when a subscription fails.

These three classes lead to the three level tree structure which stores subscriptions to BACnet objects. A single root BacnetClient instance that stores a DeviceSubscription for each BACnet device subscribed to. These then store an ObjectSubscription instance for each object subscribed to on the BACnet device.

### FastCS Tree

The root node of the FastCS tree is the BacnetController. This takes in a BacnetClient as an argument to construct the tree. This creates a BacnetSubcontroller for each DeviceSubscription connected to the BacnetClient passed in.
The BacnetSubcontroller creates a BacnetAttributeIORef for each ObjectSubscription in the equivalent DeviceSubscription. it does some descision making here of whether to create an AnalogAttributeIORef or BinaryAttributeIORef depending on the BACnet object its subscribed to. This is also where the subscription callback is set, connecting the object subscription updates to updating the relevant PV.

This process creates a FastCS tree equivalent to the BACnet tree. The BacnetClient maps to the BacnetController, every DeviceSubscription has an equivalent BacnetSubcontroller and every ObjectSubscription has an equivalent BacnetAttributeIORef.

Reads bacnet data to an IOC

This is where you should write a short paragraph that describes what your module does,
how it does it, and why people should use it.

Source          | <https://github.com/DiamondLightSource/fastcs-bacnet>
:---:           | :---:
PyPI            | `pip install fastcs-bacnet`
Docker          | `docker run ghcr.io/diamondlightsource/fastcs-bacnet:latest`
Releases        | <https://github.com/DiamondLightSource/fastcs-bacnet/releases>
Services        | <https://gitlab.diamond.ac.uk/controls/containers/accelerator/bms-services#>
Deployment      | <https://gitlab.diamond.ac.uk/controls/containers/accelerator/bms-deployment#>

This is where you should put some images or code snippets that illustrate
some relevant examples. If it is a library then you might put some
introductory code here:

```python
from fastcs_bacnet import __version__

print(f"Hello fastcs_bacnet {__version__}")
```

Or if it is a commandline tool then you might put some example commands here:

```
python -m fastcs_bacnet --version
```
