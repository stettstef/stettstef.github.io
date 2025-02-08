const crypto = require('crypto');

function hashPassword(password) {
    // Cria um hash SHA-512
    const hash = crypto.createHash('sha512');
    
    // Atualiza o hash com a senha
    hash.update(password);
    
    // Gera o hash em formato hexadecimal
    const hashedPassword = hash.digest('hex');
    
    return hashedPassword;
}

// Exemplo de uso
const password = 'Ma654783@';
const hashedPassword = hashPassword(password);

console.log('Senha original:', password);
console.log('Senha hasheada (SHA-512):', hashedPassword);