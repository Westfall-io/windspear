# windspear
Model Webhook

This sensor execution will:
1. Grab the git repo for the model and checkout the given commit id
2. Add this commit id to the windstorm database
3. Filter the model to just SysML elements and parse those elements
4. Push the model elements to the windstorm database
5. Parse the model elements for specific types to be added to specific tables
6. Add the specific model elements (reqts, verifications) to the windstorm
database
7. Update the commit id in the windstorm database that it has been completed
(this allows to see when commits are having problems in parsing)
8. Post webhook to windstorm to handle downstream events
