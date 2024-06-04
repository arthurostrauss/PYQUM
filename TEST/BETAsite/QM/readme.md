## How to setup QM

````
pip install qm-qua==1.1.6
pip install qm-octave==2.0.1
pip install qualang-tools==0.17.4
````

## Documentations
https://qm-docs.qualang.io/guides/queue

Octave documentation - https://docs.quantum-machines.co/0.1/qm-qua-sdk/docs/Guides/octave/

Octave GitHub - https://github.com/qua-platform/qua-libs/tree/main/Tutorials/intro-to-octave

#### How to access QOP202 (older firmware): 
http://192.168.1.xxx:11010 

## Re-clustering at a lower level:
1. Connect PC-LAN to port 2-10 directly
2. Check QM-Router to find OPX's internal IP:
http://192.168.88.1:81 (http://192.168.88.1:81/webfig/#IP:ARP)
3. Check QM Configurator for OPX at lower level:
http://192.168.88.xxx:1883/docs/ 
(http://192.168.88.xxx:1883/docs/#/Configurator/PostMulticlusterCreate)
4. Check the OPX using internal IP of the QM-Router:
http://192.168.88.xxx (http://192.168.88.xxx/ui/cluster)
5. If it works, you should see Admin page using the QM-Router external IP.
6. YaY

## Fixing QM-router:
1. Reset configuration on the front panel
2. Directly connect PC with QM-router on LAN port 2-10
3. Run "update_router_settings.py"
4. Restart QM-router (optional)
