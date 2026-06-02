import User from "../utils/user";


export default class TestUsers {
    static readonly Admin = new User(process.env.DEFAULT_USER_EMAIL, process.env.DEFAULT_USER_PASSWORD, 'Admin User', 'Vendor');
}