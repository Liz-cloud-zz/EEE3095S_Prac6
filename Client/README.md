## Client Code.

To get this project up and running, you will need to signup for a balena account [here][signup-page] and set up a device.
Once you are set up with balena, you will need to clone this repo locally:
```
$ git clone git@github.com:Reposave/First-Fleet.git
```
Then add your balena application's remote:
```
$ git remote add balena username@git.balena-cloud.com:username/myapp.git
```
and push the code to the newly added remote:
```
$ git push balena master
```
It should take a few minutes for the code to push. Enable device URLs so we can see the server outside of our local network. This option can be toggled on the device summary page or in the `Actions` tab in your device dashboards.

Then in your browser you should be able to open the device URL and see the message "Hello World!".
