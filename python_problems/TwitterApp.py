class Twitter(object):
    def __init__(self,name,age):
        self.name=name
        self.age=age
        self.following_list=[]
        self.follower_list=[]
        self.list_my_tweet=[]

    def add_follower(self,t):
        self.follower_list.append(t)
        t.following_list.append(self)

    def add_followed(self,t):
        self.following_list.append(t)
        t.follower_list.append(self)
        print("Now, You are following "+t.name)

    def disp_follower(self):
        for i in self.follower_list:
            print(i.name, i.age)

    def disp_followed(self):
        for i in self.following_list:
            print(i.name, i.age)


    def mytweet(self,message):
        self.message=message
        self.list_my_tweet.append(message)

    def disp_my_tweet(self,t):
        for i in self.list_my_tweet:
            print(i)

    def disp_specific_tweet(self,t):
        if self in t.follower_list:
            for i in t.list_my_tweet:
                print(i)
        else:
            print("You are not follower of " +t.name)		
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
    def get_following(self,t):
        if self in t.follower_list:
            print("You are his Follower")
        else:
            print("Sorry! You are not his Follower")
