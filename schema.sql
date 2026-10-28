CREATE DATABASE IF NOT EXISTS shopping_analysis
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE shopping_analysis;

CREATE TABLE IF NOT EXISTS products (
  product_id INT AUTO_INCREMENT PRIMARY KEY,
  product_name VARCHAR(150) NOT NULL,
  category VARCHAR(100) NOT NULL DEFAULT 'General',
  unit_price DECIMAL(10,2) NOT NULL CHECK (unit_price >= 0),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
  order_id INT AUTO_INCREMENT PRIMARY KEY,
  order_date DATE NOT NULL,
  payment_method ENUM('UPI','Card','Cash on Delivery','Net Banking','Wallet') NOT NULL,
  order_status ENUM('Pending','Processing','Shipped','Delivered','Cancelled','Refunded')
    NOT NULL DEFAULT 'Pending',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS order_items (
  item_id INT AUTO_INCREMENT PRIMARY KEY,
  order_id INT NOT NULL,
  product_id INT NOT NULL,
  quantity INT NOT NULL CHECK (quantity > 0),
  unit_price DECIMAL(10,2) NOT NULL CHECK (unit_price >= 0),
  CONSTRAINT fk_items_order FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
  CONSTRAINT fk_items_product FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Optional sample data. Run this section only once to avoid duplicate sample rows.
INSERT INTO products (product_name, category, unit_price) VALUES
('Wireless Mouse','Electronics',599.00),
('Notebook Set','Stationery',249.00),
('Water Bottle','Home',399.00),
('USB-C Cable','Electronics',299.00),
('Backpack','Accessories',1299.00);

INSERT INTO orders (order_date,payment_method,order_status) VALUES
(CURDATE() - INTERVAL 4 MONTH,'UPI','Delivered'),
(CURDATE() - INTERVAL 3 MONTH,'Card','Delivered'),
(CURDATE() - INTERVAL 2 MONTH,'Cash on Delivery','Shipped'),
(CURDATE() - INTERVAL 1 MONTH,'UPI','Cancelled'),
(CURDATE() - INTERVAL 12 DAY,'Wallet','Delivered'),
(CURDATE() - INTERVAL 5 DAY,'Net Banking','Refunded'),
(CURDATE() - INTERVAL 2 DAY,'Card','Pending');

INSERT INTO order_items (order_id,product_id,quantity,unit_price) VALUES
(1,1,2,599.00),(1,2,1,249.00),(2,5,1,1299.00),(2,4,2,299.00),
(3,3,2,399.00),(4,1,1,599.00),(5,5,1,1299.00),(5,2,3,249.00),
(6,4,1,299.00),(7,3,1,399.00);
