## real2scrap

It`s a program that has a webScrap function that takes two arguments (x= first page and y= final page).

The program makes a scrap of the site: "https://www.imovelweb.com.br" and returns a csv file with some characteristics of the property in the chosen region.

## Install - method 1

```pip install pandas```

```pip install numpy```

```pip install supabase```

```pip install python-dotenv```

```pip install selenium```

```pip install webdriver```

```pip install -i https://test.pypi.org/simple/ real2scrap```

make the import:```from real2scrap import scrap```

and run the function ```scrap()```



## Install - method 2

1 - Create a folder in the place that you want.

2 - open git bash in this folder.

3 - clone my projet using: ```git clone https://github.com/LucasAbreu89/webscrap.git```

4 - Open my folder in the program that you want, pycharm or vscode

5 - in the terminal, move to webscrap folder inside the folder that you create

6 - run in the terminal: ```pip install -r requirements.txt```

7 - create a python file inside the webscrap folder

8 - make the package import : ```from real2scrap.realstate_scrap import scrap```

9 - run the function ```scrap()``` with tha parameters that you want!



