## real2scrap

It`s a program that has a webScrap function that takes two arguments (x= first page and y= final page).

The program makes a scrap of the site: "https://www.imovelweb.com.br" and returns a csv file with some characteristics of the property in the chosen region.

<<<<<<< HEAD
## Install

We need some packeges to be installed. Open you cmd and install the packages bellow:

1- pip install pandas

2- pip install selenium

3- pip install webdriver_manager

4- pip install numpy

5- pip install supabase

#and finally

5- pip install -i https://test.pypi.org/simple/ real2scrap

If you have any doubt how to install a package in python, take a look at this tutorial: https://www.datacamp.com/tutorial/pip-python-package-manager

The package is still in testpypi until it passes your approval

After you install all this packages, open you jupyter notebook and do like the image below:

![image](https://user-images.githubusercontent.com/123965126/219512577-69e371d0-3323-400e-bd81-7a0c60c51e67.png)

After you run the program and got the msg : "Time to look at your csv file" you can take a look in your csv file like the image bellow:

![image](https://user-images.githubusercontent.com/123965126/219512754-6b2a9411-5005-4f91-8f97-1b2a3d937530.png)

note: To make the scrap of each page the program takes approximately 30 sec
=======

## Install - method 1

We need some packages to be installed. Open you cmd and install the packages bellow:

  1- pip install pandas
  
  2- pip install selenium
  
  3- pip install webdriver_manager
  
  4- pip install numpy
  
  **and finally**
  
  5- pip install -i https://test.pypi.org/simple/ real2scrap
  
If you have any doubt about how to install a package in python, take a look at this tutorial: https://www.datacamp.com/tutorial/pip-python-package-manager
  
The package is still in testpypi until it passes your approval

After you install all this packages, open you jupyter notebook and do like the image below:

![image](https://user-images.githubusercontent.com/123965126/219512577-69e371d0-3323-400e-bd81-7a0c60c51e67.png)

After you run the program and got the msg : "Time to look at your csv file" you can take a look in your csv file like the image bellow:

![image](https://user-images.githubusercontent.com/123965126/219512754-6b2a9411-5005-4f91-8f97-1b2a3d937530.png)

note: To make the scrap of each page the program takes approximately 30 sec

## Install - method 2

1 - Create a folder in the place that you want.

2 - open git bash in this folder.

3 - clone my projet using: git clone

4 - Open my folder in the program that you want, pycharm or vscode

5 - in the terminal, move to webscrap folder inside the folder that you create

6 - run in the terminal: pip install -r requirements.txt

7 - create a python file inside the webscrap folder

8 - make the package import : from real2scrap.realstate_scrap import scrap

9 - run the function scrap() with tha parameters that you want!



>>>>>>> 3a9cda69b12c6bef97968123e091f984231da3fa