export const CURRENT_USER ={
name:"Sunil Paudel",
role:"Data Analyst",
initials:"SP",
};

export function saveUser(updates) {
    Object.assign(CURRENT_USER, updates);
}