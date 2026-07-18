
You will get:



This how you install angular:
```bash
curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash # Yes nvm, not npm
source ~/.bashrc                 # nvm installation alters .bashrc 
nvm install --lts                # installs both node and npm
npm -v                           # check npm 
```


Once `npm` is available, we install the Angular command-line tools globally (global to all projects of the user):

`npm install -g @angular/cli`

Now we can actually create a project:

```bash
ng new angular_app 
cd angular_app
ng serve --open`
```
This creates a new Angular project `my-app` and moves into its folder, and then starts a development server on `http://localhost:4200`. 

Finally, create new components with.

`ng generate component habit --standalone`

Run it in your project folder `angular_app`. This will create a new component called `habit` in the `src/app` folder. 	

---

Installing the backend

```bash
cp -r resources/src/app/backend/* angular_app/src/backend/

mkdir -p src/backend/habit

touch src/backend/main.py
touch src/backend/database.py
touch src/backend/models.py
touch src/backend/schemas.py
touch src/backend/jwt_tokens.py

touch src/backend/auth/__init__.py
touch src/backend/auth/auth.py

touch src/backend/habit/__init__.py
touch src/backend/habit/habit.py
```